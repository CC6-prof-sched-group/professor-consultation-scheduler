"""
URL configuration for consultation_scheduler project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter
from accounts.views import AuthViewSet, ProfileViewSet
from consultations.views import ConsultationSlotViewSet, BookingViewSet, ConsultationNoteViewSet, google_calendar_auth, google_calendar_callback

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'slots', ConsultationSlotViewSet, basename='consultationslot')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'notes', ConsultationNoteViewSet, basename='consultationnote')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/google/auth/', google_calendar_auth, name='google-auth'),
    path('api/google/callback/', google_calendar_callback, name='google-callback'),
    path('', RedirectView.as_view(url='/api/', permanent=False)),
]