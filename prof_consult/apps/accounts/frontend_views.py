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
    
    # Get recent notifications
    notifications = Notification.objects.filter(
        user=user
    ).order_by('-created_at')[:5]
    
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
            status__in=[ConsultationStatus.PENDING, ConsultationStatus.CONFIRMED],
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
    
    context = {
        'consultations': consultations,
        'status_filter': status_filter,
    }
    
    return render(request, 'consultations.html', context)


@login_required
def book_consultation(request):
    """
    Book a new consultation.
    Displays booking form and handles form submission.
    """
    if request.method == 'POST':
        # Get form data
        professor_id = request.POST.get('professor')
        date = request.POST.get('date')
        time = request.POST.get('time')
        consultation_type = request.POST.get('type', 'in_person')
        subject = request.POST.get('subject')
        notes = request.POST.get('notes', '')
        
        # Validate and create consultation
        try:
            professor = User.objects.get(id=professor_id, role=Role.PROFESSOR)
            
            # Create consultation
            consultation = Consultation.objects.create(
                student=request.user,
                professor=professor,
                title=subject,
                description=notes,
                scheduled_date=date,
                scheduled_time=time,
                status=ConsultationStatus.PENDING,
                location='Online' if consultation_type == 'online' else professor.professor_profile.office_location
            )
            
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
    ).select_related('professor_profile')
    
    context = {
        'professors': professors,
    }
    
    return render(request, 'book_consultation.html', context)


def professors_list(request):
    """
    List all available professors.
    Supports search and department filtering.
    """
    search_query = request.GET.get('search', '')
    department_filter = request.GET.get('department', '')
    
    # Base queryset
    professors = User.objects.filter(
        role=Role.PROFESSOR,
        is_active=True
    ).select_related('professor_profile')
    
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
        
        # Calculate average rating
        avg_rating = Consultation.objects.filter(
            professor=professor,
            rating__isnull=False
        ).aggregate(Avg('rating'))['rating__avg']
        professor.avg_rating = round(avg_rating, 1) if avg_rating else 0
    
    context = {
        'professors': professors,
        'departments': [d for d in departments if d],
        'search_query': search_query,
        'department_filter': department_filter,
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
    
    try:
        profile = professor.professor_profile
    except ProfessorProfile.DoesNotExist:
        raise Http404("Professor profile not found")
    
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
    ).exclude(feedback='').order_by('-completed_at')[:5]
    
    context = {
        'professor': professor,
        'profile': profile,
        'total_consultations': total_consultations,
        'this_month_consultations': this_month_consultations,
        'avg_rating': round(avg_rating, 1) if avg_rating else 0,
        'rating_count': recent_reviews.count(),
        'recent_reviews': recent_reviews,
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
            available_days = {}
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day in days:
                enabled = request.POST.get(f'{day}_enabled')
                if enabled == 'on':
                    start_time = request.POST.get(f'{day}_start')
                    end_time = request.POST.get(f'{day}_end')
                    if start_time and end_time:
                        available_days[day] = [{
                            'start': start_time,
                            'end': end_time
                        }]
            
            profile.available_days = available_days
            profile.save()
            
            messages.success(request, 'Availability settings updated successfully!')
            return redirect('professor_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error updating settings: {str(e)}')
    
    context = {
        'profile': profile,
        'available_days_json': json.dumps(profile.available_days) if profile.available_days else '{}',
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
            
            # Create notification for student
            Notification.objects.create(
                user=consultation.student,
                message=f'Your consultation with {user.get_full_name()} has been confirmed.',
                notification_type='CONSULTATION_CONFIRMED'
            )
            
        elif action == 'cancel':
            reason = request.POST.get('reason', '')
            consultation.status = ConsultationStatus.CANCELLED
            consultation.cancelled_at = timezone.now()
            consultation.cancellation_reason = reason
            consultation.save()
            messages.success(request, 'Consultation cancelled.')
            
            # Create notification for student
            Notification.objects.create(
                user=consultation.student,
                message=f'Your consultation with {user.get_full_name()} has been cancelled.',
                notification_type='CONSULTATION_CANCELLED'
            )
        
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
