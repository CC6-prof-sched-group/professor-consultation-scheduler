"""
Frontend views for professor consultation scheduler.
Renders HTML templates with data from models.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.http import Http404
from datetime import datetime, timedelta

from apps.accounts.models import User, Role
from apps.consultations.models import Consultation, ConsultationStatus
from apps.professors.models import ProfessorProfile
from apps.notifications.models import Notification
from apps.notifications.tasks import (
    send_booking_created_notification,
    send_booking_confirmed_notification,
    send_booking_cancelled_notification,
    send_booking_rescheduled_notification,
    send_reschedule_proposal_notification
)
import json


def home(request):
    """
    Homepage view.
    Displays welcome page with features and quick actions based on user role.
    """
    context = {
        'user': request.user,
    }
    return render(request, 'home.html', context)


def login_view(request):
    """
    Login page view.
    Redirects to home if already authenticated.
    """
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'login.html')


@login_required
def dashboard(request):
    """
    User dashboard view.
    Redirects to appropriate dashboard based on user role.
    """
    user = request.user
    
    # Redirect professors to professor dashboard
    if user.role == Role.PROFESSOR:
        return redirect('professor_dashboard')
    
    # Student dashboard
    # Get consultations based on user role
    if user.role == Role.STUDENT:
        consultations = Consultation.objects.filter(student=user)
    else:
        # Admin view - show all
        consultations = Consultation.objects.all()
    
    # Calculate statistics
    total_consultations = consultations.count()
    upcoming = consultations.filter(
        status__in=[ConsultationStatus.PENDING, ConsultationStatus.CONFIRMED],
        scheduled_date__gte=timezone.now().date()
    ).count()
    pending = consultations.filter(status=ConsultationStatus.PENDING).count()
    this_month = consultations.filter(
        scheduled_date__year=timezone.now().year,
        scheduled_date__month=timezone.now().month
    ).count()
    
    # Get upcoming consultations (next 5)
    upcoming_consultations = consultations.filter(
        status__in=[ConsultationStatus.PENDING, ConsultationStatus.CONFIRMED],
        scheduled_date__gte=timezone.now().date()
    ).order_by('scheduled_date', 'scheduled_time')[:5]
    # Avoid N+1 queries when rendering user names and social account data
    try:
        upcoming_consultations = upcoming_consultations.select_related('student', 'professor').prefetch_related(
            'student__socialaccount_set', 'professor__socialaccount_set'
        )
    except Exception:
        # If slicing produced a list-like object that doesn't support queryset methods,
        # skip prefetching (best-effort optimization).
        pass
    
    # Get recent notifications
    notifications = Notification.objects.filter(
        user=user
    ).order_by('-created_at')[:5]
    
    top_professors = User.objects.filter(
        role=Role.PROFESSOR,
        is_active=True,
        professor_profile__total_reviews__gt=0
    ).select_related('professor_profile').prefetch_related('socialaccount_set').order_by(
        '-professor_profile__average_rating'
    )[:5]
    context = {
        'total_consultations': total_consultations,
        'upcoming': upcoming,
        'pending': pending,
        'this_month': this_month,
        'upcoming_consultations': upcoming_consultations,
        'notifications': notifications,
    }
    
    return render(request, 'dashboard.html', context)


@login_required
def consultations_list(request):
    """
    List all consultations for the current user.
    Filterable by status (upcoming, past, cancelled).
    """
    user = request.user
    status_filter = request.GET.get('status', 'upcoming')
    
    # Base queryset based on user role
    if user.role == Role.STUDENT:
        base_qs = Consultation.objects.filter(student=user)
    elif user.role == Role.PROFESSOR:
        base_qs = Consultation.objects.filter(professor=user)
    else:
        base_qs = Consultation.objects.all()
    
    # Filter by status
    today = timezone.now().date()
    if status_filter == 'upcoming':
        consultations = base_qs.filter(
            status__in=[
                ConsultationStatus.PENDING, 
                ConsultationStatus.CONFIRMED, 
                ConsultationStatus.RESCHEDULE_PROPOSED
            ],
            scheduled_date__gte=today
        ).order_by('scheduled_date', 'scheduled_time')
    elif status_filter == 'past':
        consultations = base_qs.filter(
            Q(status=ConsultationStatus.COMPLETED) |
            Q(scheduled_date__lt=today)
        ).order_by('-scheduled_date', '-scheduled_time')
    elif status_filter == 'cancelled':
        consultations = base_qs.filter(
            status=ConsultationStatus.CANCELLED
        ).order_by('-scheduled_date', '-scheduled_time')
    else:
        consultations = base_qs.order_by('-scheduled_date', '-scheduled_time')
    
    # Optimize query with select_related to avoid N+1 queries
    consultations = consultations.select_related('student', 'professor')
    
    context = {
        'consultations': consultations,
        'status_filter': status_filter,
    }
    
    return render(request, 'consultations.html', context)


@login_required
def consultation_detail(request, consultation_id):
    """
    Display a single consultation/booking detail for frontend.
    Permissions: only the student, the professor, or an admin can view.
    Provides context flags to enable reschedule/cancel actions in the template.
    """
    consultation = get_object_or_404(Consultation, id=consultation_id)

    user = request.user
    # Allow student, professor, or admin
    if not (
        user == consultation.student or
        user == consultation.professor or
        user.role == Role.ADMIN
    ):
        raise Http404()

    can_cancel = False
    try:
        can_cancel = consultation.can_be_cancelled()
    except Exception:
        # Best-effort: if method not present or errors, default False
        can_cancel = False

    can_reschedule = consultation.status == ConsultationStatus.CONFIRMED

    context = {
        'consultation': consultation,
        'can_cancel': can_cancel,
        'can_reschedule': can_reschedule,
    }

    return render(request, 'consultation_detail.html', context)


@login_required
def book_consultation(request):
    """
    Book a new consultation.
    Displays booking form and handles form submission.
    """
    selected_professor_id = request.GET.get('professor')

    if request.method == 'POST':
        # Get form data
        professor_id = request.POST.get('professor')
        date = request.POST.get('date')
        time = request.POST.get('time')
        consultation_type = request.POST.get('type', 'in_person')
        subject = request.POST.get('subject')
        notes = request.POST.get('notes', '')
        duration = request.POST.get('duration', 30)
        is_special_request = request.POST.get('is_special_request') == 'true'
        special_reason = request.POST.get('special_request_reason')
        selected_professor_id = professor_id
        
        # Validate and create consultation
        try:
            professor = User.objects.get(id=professor_id, role=Role.PROFESSOR)
            
            # If special request, append reason to notes
            if is_special_request and special_reason:
                notes = f"[SPECIAL REQUEST] Reason: {special_reason}\n\n{notes}"
            
            # Create consultation
            consultation = Consultation.objects.create(
                student=request.user,
                professor=professor,
                title=subject,
                description=notes,
                scheduled_date=date,
                scheduled_time=time,
                duration=duration,
                is_special_request=is_special_request,
                status=ConsultationStatus.PENDING,
                location='Online' if consultation_type == 'online' else professor.professor_profile.office_location
            )
            
            # Send notifications (emails + in-app)
            send_booking_created_notification(consultation.id)
            
            messages.success(request, 'Consultation booked successfully! Waiting for professor confirmation.')
            return redirect('consultations_list')
            
        except User.DoesNotExist:
            messages.error(request, 'Invalid professor selected.')
        except Exception as e:
            messages.error(request, f'Error booking consultation: {str(e)}')
    
    # Get available professors
    professors = User.objects.filter(
        role=Role.PROFESSOR,
        is_active=True
    ).select_related('professor_profile').prefetch_related('socialaccount_set')
    
    context = {
        'professors': professors,
        'selected_professor_id': str(selected_professor_id) if selected_professor_id else '',
    }
    
    return render(request, 'book_consultation.html', context)


def professors_list(request):
    """
    List all available professors.
    Supports search and department filtering.
    """
    search_query = request.GET.get('search', '')
    department_filter = request.GET.get('department', '')
    sort_by = request.GET.get('sort', 'rating')  # NEW: sorting
    
    # Base queryset
    professors = User.objects.filter(
        role=Role.PROFESSOR,
        is_active=True
    ).select_related('professor_profile').prefetch_related('socialaccount_set')
    
    # Apply search filter
    if search_query:
        professors = professors.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(department__icontains=search_query)
        )
    
    # Apply department filter
    if department_filter:
        professors = professors.filter(department=department_filter)
    
    # Get unique departments for filter dropdown
    departments = User.objects.filter(
        role=Role.PROFESSOR,
        is_active=True
    ).values_list('department', flat=True).distinct()
    
    # Add consultation stats
    for professor in professors:
        professor.total_consultations = Consultation.objects.filter(
            professor=professor,
            status=ConsultationStatus.COMPLETED
        ).count()
    
    # NEW: Sort professors
    if sort_by == 'rating':
        professors = sorted(professors, key=lambda p: (
            -p.professor_profile.average_rating if hasattr(p, 'professor_profile') else 0,
            p.last_name or ''
        ))
    elif sort_by == 'reviews':
        professors = sorted(professors, key=lambda p: (
            -p.professor_profile.total_reviews if hasattr(p, 'professor_profile') else 0
        ))
    elif sort_by == 'name':
        professors = sorted(professors, key=lambda p: p.last_name or p.first_name or '')
    
    context = {
        'professors': professors,
        'departments': [d for d in departments if d],
        'search_query': search_query,
        'department_filter': department_filter,
        'sort_by': sort_by,
    }
    
    return render(request, 'professors_list.html', context)


def professor_profile(request, professor_id):
    """
    Display detailed professor profile.
    Shows bio, expertise, office hours, and reviews.
    """
    professor = get_object_or_404(
        User,
        id=professor_id,
        role=Role.PROFESSOR,
        is_active=True
    )
    
    profile, created = ProfessorProfile.objects.get_or_create(
        user=professor,
        defaults={
            'title': 'Prof.',
            'department': professor.department or 'General',
            'office_location': 'Office TBD',
            'consultation_duration_default': 60,
            'max_advance_booking_days': 30,
            'buffer_time_between_consultations': 15,
            'status': 'AVAILABLE'
        }
    )
    
    # Get statistics
    total_consultations = Consultation.objects.filter(
        professor=professor,
        status=ConsultationStatus.COMPLETED
    ).count()
    
    # Get statistics
    total_consultations = Consultation.objects.filter(
        professor=professor,
        status=ConsultationStatus.COMPLETED
    ).count()
    
    this_month_consultations = Consultation.objects.filter(
        professor=professor,
        scheduled_date__year=timezone.now().year,
        scheduled_date__month=timezone.now().month
    ).count()
    
    # Calculate average rating
    avg_rating = Consultation.objects.filter(
        professor=professor,
        rating__isnull=False
    ).aggregate(Avg('rating'))['rating__avg']
    
    # Get recent reviews
    recent_reviews = Consultation.objects.filter(
        professor=professor,
        rating__isnull=False,
        feedback__isnull=False
    ).exclude(feedback='').order_by('-updated_at')[:5]
    try:
        recent_reviews = recent_reviews.select_related('student').prefetch_related('student__socialaccount_set')
    except Exception:
        pass
    
    from django.db.models import Count
    rating_counts = {}
    rating_breakdown = {}
    
    if profile.total_reviews > 0:
        ratings = Consultation.objects.filter(
            professor=professor,
            rating__isnull=False
        ).values('rating').annotate(count=Count('rating'))
        
        for item in ratings:
            rating_counts[item['rating']] = item['count']
            rating_breakdown[item['rating']] = (item['count'] / profile.total_reviews) * 100
    
    context = {
        'professor': professor,
        'profile': profile,
        'total_consultations': total_consultations,
        'this_month_consultations': this_month_consultations,
        'recent_reviews': recent_reviews,
        'rating_counts': rating_counts,  # NEW
        'rating_breakdown': rating_breakdown,  # NEW
    }
    
    return render(request, 'professor_profile.html', context)


@login_required
def profile_settings(request):
    """
    User profile and settings page.
    Allows users to update their profile information and preferences.
    """
    user = request.user
    
    if request.method == 'POST':
        # Handle form submission
        tab = request.POST.get('tab', 'profile')
        
        if tab == 'profile':
            # Update profile information
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.department = request.POST.get('department', user.department)
            user.bio = request.POST.get('bio', user.bio)
            user.save()
            
            messages.success(request, 'Profile updated successfully!')
        
        elif tab == 'notifications':
            # Update notification preferences
            # This would update user preferences model if you have one
            messages.success(request, 'Notification preferences updated!')
        
        return redirect('profile_settings')
    
    # Get connected accounts
    social_accounts = user.socialaccount_set.all() if hasattr(user, 'socialaccount_set') else []
    
    context = {
        'user': user,
        'social_accounts': social_accounts,
    }
    
    return render(request, 'profile_settings.html', context)


@login_required
def convert_to_professor(request):
    """
    Convert a student account to a professor account for testing purposes.
    Creates a professor profile and changes the user's role.
    """
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('profile_settings')
    
    user = request.user
    
    # Check if user is already a professor
    if user.role == Role.PROFESSOR:
        messages.info(request, 'You are already a professor!')
        return redirect('profile_settings')
    
    # Check if user is an admin (admins shouldn't be converted)
    if user.role == Role.ADMIN:
        messages.error(request, 'Admin accounts cannot be converted to professor accounts.')
        return redirect('profile_settings')
    
    try:
        # Change user role to professor
        user.role = Role.PROFESSOR
        user.save()
        
        # Create professor profile if it doesn't exist
        if not hasattr(user, 'professor_profile'):
            ProfessorProfile.objects.create(
                user=user,
                title='Prof.',
                department=user.department or 'General',
                office_location='Office TBD',
                consultation_duration_default=60,
                max_advance_booking_days=30,
                buffer_time_between_consultations=15,
                status='AVAILABLE'
            )
        
        messages.success(request, 
            'Your account has been successfully converted to a professor account! '
            'You can now access the professor dashboard and set your availability.'
        )
        return redirect('professor_dashboard')
        
    except Exception as e:
        messages.error(request, f'Error converting account: {str(e)}')
        return redirect('profile_settings')


def custom_404(request, exception):
    """Custom 404 error page."""
    return render(request, '404.html', status=404)


def custom_500(request):
    """Custom 500 error page."""
    return render(request, '500.html', status=500)


@login_required
def professor_dashboard(request):
    """
    Professor dashboard view.
    Shows consultation requests, statistics, and availability management.
    """
    user = request.user
    
    # Ensure user is a professor
    if user.role != Role.PROFESSOR:
        messages.error(request, 'Access denied. This page is for professors only.')
        return redirect('dashboard')
    
    # Get or create professor profile
    try:
        profile = user.professor_profile
    except ProfessorProfile.DoesNotExist:
        profile = ProfessorProfile.objects.create(user=user)
    
    # Get consultations for professor
    consultations = Consultation.objects.filter(professor=user)
    
    # Calculate statistics
    total_consultations = consultations.count()
    pending_requests = consultations.filter(status=ConsultationStatus.PENDING).count()
    confirmed_upcoming = consultations.filter(
        status=ConsultationStatus.CONFIRMED,
        scheduled_date__gte=timezone.now().date()
    ).count()
    completed_this_month = consultations.filter(
        status=ConsultationStatus.COMPLETED,
        scheduled_date__year=timezone.now().year,
        scheduled_date__month=timezone.now().month
    ).count()
    
    # Get pending consultation requests (need action)
    pending_consultations = consultations.filter(
        status=ConsultationStatus.PENDING
    ).order_by('scheduled_date', 'scheduled_time')[:10]
    
    # Get upcoming confirmed consultations
    upcoming_consultations = consultations.filter(
        status=ConsultationStatus.CONFIRMED,
        scheduled_date__gte=timezone.now().date()
    ).order_by('scheduled_date', 'scheduled_time')[:10]
    
    # Get recent notifications
    notifications = Notification.objects.filter(
        user=user
    ).order_by('-created_at')[:5]
    
    # Calculate average rating
    avg_rating = consultations.filter(
        rating__isnull=False
    ).aggregate(Avg('rating'))['rating__avg']
    
    context = {
        'profile': profile,
        'total_consultations': total_consultations,
        'pending_requests': pending_requests,
        'confirmed_upcoming': confirmed_upcoming,
        'completed_this_month': completed_this_month,
        'pending_consultations': pending_consultations,
        'upcoming_consultations': upcoming_consultations,
        'notifications': notifications,
        'avg_rating': round(avg_rating, 1) if avg_rating else 0,
        'available_days_json': json.dumps(profile.available_days) if profile.available_days else '{}',
    }
    
    return render(request, 'professor_dashboard.html', context)


@login_required
def professor_availability_settings(request):
    """
    View for professors to manage their availability settings.
    """
    user = request.user
    
    # Ensure user is a professor
    if user.role != Role.PROFESSOR:
        messages.error(request, 'Access denied. This page is for professors only.')
        return redirect('dashboard')
    
    # Get or create professor profile
    try:
        profile = user.professor_profile
    except ProfessorProfile.DoesNotExist:
        profile = ProfessorProfile.objects.create(user=user)
    
    if request.method == 'POST':
        try:
            # Update consultation preferences
            profile.consultation_duration_default = int(request.POST.get('consultation_duration', 30))
            profile.buffer_time_between_consultations = int(request.POST.get('buffer_time', 15))
            profile.max_advance_booking_days = int(request.POST.get('max_advance_booking_days', 30))
            profile.office_location = request.POST.get('office_location', '')
            profile.title = request.POST.get('title', '')
            profile.department = request.POST.get('department', '')
            
            # Update availability
            # Update availability
            available_days = {}
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day in days:
                enabled = request.POST.get(f'{day}_enabled')
                if enabled == 'on':
                    start_times = request.POST.getlist(f'{day}_start')
                    end_times = request.POST.getlist(f'{day}_end')
                    
                    day_slots = []
                    for s, e in zip(start_times, end_times):
                        if s and e:
                            # Basic validation: start < end? 
                            # We can just save it for now, logic elsewhere handles validity or UI can enforce
                            day_slots.append({
                                'start': s,
                                'end': e
                            })
                    
                    if day_slots:
                        available_days[day] = day_slots
            
            profile.available_days = available_days
            profile.save()
            
            messages.success(request, 'Availability settings updated successfully!')
            return redirect('professor_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error updating settings: {str(e)}')
    
    days_mapping = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    context = {
        'profile': profile,
        'available_days_json': json.dumps(profile.available_days) if profile.available_days else '{}',
        'days_mapping': days_mapping,
    }
    
    return render(request, 'professor_availability_settings.html', context)


@login_required
def professor_consultation_action(request, consultation_id):
    """
    Handle professor actions on consultations (confirm/cancel).
    """
    user = request.user
    
    # Ensure user is a professor
    if user.role != Role.PROFESSOR:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    consultation = get_object_or_404(Consultation, id=consultation_id, professor=user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'confirm':
            consultation.status = ConsultationStatus.CONFIRMED
            consultation.confirmed_at = timezone.now()
            consultation.save()
            messages.success(request, 'Consultation confirmed!')
            
            # Send notifications
            send_booking_confirmed_notification(consultation.id)
            
        elif action == 'cancel':
            reason = request.POST.get('reason', '')
            consultation.status = ConsultationStatus.CANCELLED
            consultation.cancelled_at = timezone.now()
            consultation.cancellation_reason = reason
            consultation.save()
            messages.success(request, 'Consultation cancelled.')
            
            # Send notifications
            send_booking_cancelled_notification(consultation.id, reason)

        elif action == 'reschedule':
            new_time = request.POST.get('new_time')
            if new_time:
                consultation.status = ConsultationStatus.RESCHEDULE_PROPOSED
                consultation.scheduled_time = new_time
                consultation.save()
                messages.success(request, 'Reschedule proposal sent to student.')
                
                # Send notifications
                send_reschedule_proposal_notification(consultation.id)
            else:
                messages.error(request, 'New time is required for rescheduling.')
        
        return redirect('professor_dashboard')
    
    return redirect('professor_dashboard')


@login_required
def professor_change_status(request):
    """
    Change professor's availability status.
    """
    user = request.user
    
    # Ensure user is a professor
    if user.role != Role.PROFESSOR:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get or create professor profile
    try:
        profile = user.professor_profile
    except ProfessorProfile.DoesNotExist:
        profile = ProfessorProfile.objects.create(user=user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        
        # Import ProfessorStatus from models
        from apps.professors.models import ProfessorStatus
        
        # Validate status
        valid_statuses = [choice[0] for choice in ProfessorStatus.choices]
        if new_status in valid_statuses:
            profile.status = new_status
            profile.save()
            messages.success(request, f'Status updated to {ProfessorStatus(new_status).label}!')
        else:
            messages.error(request, 'Invalid status selected.')
    
    return redirect('professor_dashboard')
@login_required
def rate_consultation(request, consultation_id):
    """
    Handle consultation rating submission.
    Students can rate completed consultations.
    """
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('consultations_list')
    
    # Get consultation
    consultation = get_object_or_404(Consultation, id=consultation_id)
    
    # Verify student owns this consultation
    if consultation.student != request.user:
        messages.error(request, 'You can only rate your own consultations.')
        return redirect('consultations_list')
    
    # Verify consultation is completed
    if consultation.status != ConsultationStatus.COMPLETED:
        messages.error(request, 'You can only rate completed consultations.')
        return redirect('consultations_list')
    
    try:
        # Get rating data
        rating = int(request.POST.get('rating', 0))
        feedback = request.POST.get('feedback', '').strip()
        anonymous = request.POST.get('anonymous') == 'on'
        
        # Validate rating
        if rating < 1 or rating > 5:
            messages.error(request, 'Rating must be between 1 and 5 stars.')
            return redirect('consultations_list')
        
        # Update consultation
        consultation.rating = rating
        consultation.feedback = feedback
        consultation.save()
        
        # The signal will automatically update professor's average rating
        # But we can also manually trigger it for immediate sync
        if hasattr(consultation.professor, 'professor_profile'):
            avg_rating, total_reviews = consultation.professor.professor_profile.calculate_ratings()
            
            messages.success(
                request, 
                f'Thank you for rating! Your {rating}-star review has been submitted. '
                f'Professor {consultation.professor|display_name} now has {avg_rating}★ average from {total_reviews} reviews.'
            )
        else:
            messages.success(request, f'Thank you for your {rating}-star rating!')
        
    except ValueError:
        messages.error(request, 'Invalid rating value.')
    except Exception as e:
        messages.error(request, f'Error submitting rating: {str(e)}')
    
    return redirect('consultations_list')


@login_required
def student_consultation_action(request, consultation_id):
    """
    Handle student actions on consultations (accept/reject reschedule).
    """
    user = request.user
    consultation = get_object_or_404(Consultation, id=consultation_id, student=user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'accept_reschedule':
            consultation.status = ConsultationStatus.CONFIRMED
            consultation.confirmed_at = timezone.now()
            consultation.save()
            messages.success(request, 'Reschedule accepted! Consultation confirmed.')
            
            # Notify Professor (and student confirmation)
            send_booking_rescheduled_notification(consultation.id)
            
        elif action == 'reject_reschedule':
            consultation.status = ConsultationStatus.CANCELLED
            consultation.cancelled_at = timezone.now()
            consultation.cancellation_reason = "Student rejected reschedule proposal."
            consultation.save()
            messages.success(request, 'Reschedule rejected. Consultation cancelled.')
            
            # Notify Professor
            send_booking_cancelled_notification(consultation.id, "Student rejected reschedule proposal.")
            
    return redirect('consultation_detail', consultation_id=consultation.id)