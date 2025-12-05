"""
URL configuration for prof_consult project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views

from apps.accounts.views import UserViewSet
from apps.consultations.views import ConsultationViewSet
from apps.professors.views import ProfessorProfileViewSet
from apps.notifications.views import NotificationViewSet
from apps.consultations.views import CancellationRecordViewSet, RescheduleRequestViewSet
from apps.accounts import views as auth_views
from apps.accounts import frontend_views

# API Router
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'consultations', ConsultationViewSet, basename='consultation')
router.register(r'consultation-cancellations', CancellationRecordViewSet, basename='consultationcancellation')
router.register(r'consultation-reschedules', RescheduleRequestViewSet, basename='consultationreschedule')
router.register(r'professors', ProfessorProfileViewSet, basename='professor')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Frontend Pages
    path('', frontend_views.home, name='home'),
    path('login/', frontend_views.login_view, name='login'),
    path('dashboard/', frontend_views.dashboard, name='dashboard'),
    path('consultations/', frontend_views.consultations_list, name='consultations_list'),
    path('consultations/book/', frontend_views.book_consultation, name='book_consultation'),
    path('professors/', frontend_views.professors_list, name='professors_list'),
    path('professors/<int:professor_id>/', frontend_views.professor_profile, name='professor_profile'),
    path('profile/settings/', frontend_views.profile_settings, name='profile_settings'),
    
    # Professor Dashboard
    path('professor/dashboard/', frontend_views.professor_dashboard, name='professor_dashboard'),
    path('professor/availability/', frontend_views.professor_availability_settings, name='professor_availability_settings'),
    path('professor/consultation/<int:consultation_id>/action/', frontend_views.professor_consultation_action, name='professor_consultation_action'),
    path('professor/status/change/', frontend_views.professor_change_status, name='professor_change_status'),
    
    # API URLs
    path('api/', include(router.urls)),
    path('api/auth/token/', views.obtain_auth_token, name='api-token'),
    path('api/auth/user/', UserViewSet.as_view({'get': 'me'}), name='api-user'),
    
    # Authentication URLs
    path('accounts/', include('allauth.urls')),
    
    # API Authentication
    path('api/auth/google/', auth_views.GoogleOAuthView.as_view(), name='google-oauth'),
    path('api/auth/google/callback/', auth_views.GoogleOAuthCallbackView.as_view(), name='google-oauth-callback'),
    path('api/auth/logout/', auth_views.LogoutView.as_view(), name='api-logout'),
    
    # Admin API endpoints
    path('api/admin/users/', auth_views.AdminUserListView.as_view(), name='admin-users'),
    path('api/admin/consultations/', auth_views.AdminConsultationListView.as_view(), name='admin-consultations'),
    path('api/admin/statistics/', auth_views.AdminStatisticsView.as_view(), name='admin-statistics'),
    path('api/admin/users/<int:pk>/role/', auth_views.AdminUpdateUserRoleView.as_view(), name='admin-update-role'),
]

# Custom error handlers
handler404 = 'apps.accounts.frontend_views.custom_404'
handler500 = 'apps.accounts.frontend_views.custom_500'

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
