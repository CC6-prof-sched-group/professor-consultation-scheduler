"""
Admin API views for the consultation system.
"""
from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from apps.accounts.permissions import IsAdmin
from apps.accounts.serializers import UserSerializer, UserDetailSerializer
from apps.consultations.models import Consultation, ConsultationStatus
from apps.consultations.serializers import ConsultationSerializer
from apps.professors.models import ProfessorProfile

User = get_user_model()


class AdminUserListView(views.APIView):
    """List all users (admin only)."""
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """Get all users with optional filters."""
        users = User.objects.all()
        
        # Filters
        role = request.query_params.get('role')
        if role:
            users = users.filter(role=role)
        
        department = request.query_params.get('department')
        if department:
            users = users.filter(department=department)
        
        search = request.query_params.get('search')
        if search:
            users = users.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        serializer = UserDetailSerializer(users, many=True)
        return Response(serializer.data)


class AdminConsultationListView(views.APIView):
    """List all consultations (admin only)."""
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """Get all consultations with advanced filters."""
        consultations = Consultation.objects.select_related('student', 'professor').all()
        
        # Filters
        status_filter = request.query_params.get('status')
        if status_filter:
            consultations = consultations.filter(status=status_filter)
        
        professor_id = request.query_params.get('professor_id')
        if professor_id:
            consultations = consultations.filter(professor_id=professor_id)
        
        student_id = request.query_params.get('student_id')
        if student_id:
            consultations = consultations.filter(student_id=student_id)
        
        date_from = request.query_params.get('date_from')
        if date_from:
            consultations = consultations.filter(scheduled_date__gte=date_from)
        
        date_to = request.query_params.get('date_to')
        if date_to:
            consultations = consultations.filter(scheduled_date__lte=date_to)
        
        serializer = ConsultationSerializer(consultations, many=True)
        return Response(serializer.data)


class AdminStatisticsView(views.APIView):
    """Get dashboard statistics (admin only)."""
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """Get statistics for admin dashboard."""
        now = timezone.now()
        today = now.date()
        this_month_start = today.replace(day=1)
        
        stats = {
            'total_users': User.objects.count(),
            'total_students': User.objects.filter(role='STUDENT').count(),
            'total_professors': User.objects.filter(role='PROFESSOR').count(),
            'total_consultations': Consultation.objects.count(),
            'pending_consultations': Consultation.objects.filter(status=ConsultationStatus.PENDING).count(),
            'confirmed_consultations': Consultation.objects.filter(status=ConsultationStatus.CONFIRMED).count(),
            'completed_consultations': Consultation.objects.filter(status=ConsultationStatus.COMPLETED).count(),
            'cancelled_consultations': Consultation.objects.filter(status=ConsultationStatus.CANCELLED).count(),
            'consultations_today': Consultation.objects.filter(scheduled_date=today).count(),
            'consultations_this_month': Consultation.objects.filter(
                scheduled_date__gte=this_month_start
            ).count(),
            'avg_rating': Consultation.objects.filter(
                rating__isnull=False
            ).aggregate(avg=Count('rating'))['avg'] or 0,
        }
        
        return Response(stats)


class AdminUpdateUserRoleView(views.APIView):
    """Update user role (admin only)."""
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def patch(self, request, pk):
        """Update user role."""
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        role = request.data.get('role')
        if role not in [choice[0] for choice in User.Role.choices]:
            return Response(
                {'error': f'Invalid role. Must be one of: {[c[0] for c in User.Role.choices]}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.role = role
        user.save()
        
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)

