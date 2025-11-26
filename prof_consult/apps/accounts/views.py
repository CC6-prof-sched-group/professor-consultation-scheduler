"""
Views for accounts app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import views as rest_views
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import login

from apps.accounts.serializers import UserSerializer, UserDetailSerializer
from apps.accounts.permissions import IsOwnerOrReadOnly, IsAdmin
from apps.accounts.admin_views import (
    AdminUserListView, AdminConsultationListView,
    AdminStatisticsView, AdminUpdateUserRoleView
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'retrieve' or self.action == 'me':
            return UserDetailSerializer
        return UserSerializer
    
    def get_permissions(self):
        """Return appropriate permissions."""
        if self.action == 'create':
            return [AllowAny()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrReadOnly()]
        if self.action == 'list':
            return [IsAdmin()]
        return super().get_permissions()
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user details."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsOwnerOrReadOnly])
    def update_profile(self, request, pk=None):
        """Update user profile."""
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class GoogleOAuthView(rest_views.APIView):
    """Initiate Google OAuth2 flow."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Start OAuth flow."""
        from apps.integrations.services import get_google_oauth_flow
        from django.conf import settings
        
        try:
            flow = get_google_oauth_flow()
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            # Store state in session
            request.session['oauth_state'] = state
            
            return Response({
                'authorization_url': authorization_url,
                'state': state
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to initiate OAuth flow: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GoogleOAuthCallbackView(rest_views.APIView):
    """Handle Google OAuth2 callback."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Process OAuth callback."""
        from apps.integrations.services import get_google_oauth_flow
        from django.conf import settings
        
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        
        if not code:
            return Response(
                {'error': 'Authorization code not provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify state
        session_state = request.session.get('oauth_state')
        if state != session_state:
            return Response(
                {'error': 'Invalid state parameter.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            flow = get_google_oauth_flow()
            flow.fetch_token(code=code)
            
            credentials = flow.credentials
            
            # Get user info from Google
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            
            creds = Credentials(token=credentials.token)
            service = build('oauth2', 'v2', credentials=creds)
            user_info = service.userinfo().get().execute()
            
            # Get or create user
            google_id = user_info.get('id')
            email = user_info.get('email')
            
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'first_name': user_info.get('given_name', ''),
                    'last_name': user_info.get('family_name', ''),
                    'profile_picture': user_info.get('picture', ''),
                    'role': 'STUDENT',
                }
            )
            
            # Update Google OAuth info
            user.google_id = google_id
            user.google_access_token = credentials.token
            if credentials.refresh_token:
                user.google_refresh_token = credentials.refresh_token
            if not user.profile_picture:
                user.profile_picture = user_info.get('picture', '')
            user.save()
            
            # Login user
            login(request, user)
            
            # Create or get auth token
            from rest_framework.authtoken.models import Token
            token, created = Token.objects.get_or_create(user=user)
            
            serializer = UserDetailSerializer(user)
            return Response({
                'user': serializer.data,
                'token': token.key,
                'created': created
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to process OAuth callback: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LogoutView(rest_views.APIView):
    """Logout user."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Logout and delete token."""
        from rest_framework.authtoken.models import Token
        from django.contrib.auth import logout
        from django.shortcuts import redirect
        
        try:
            token = Token.objects.get(user=request.user)
            token.delete()
        except Token.DoesNotExist:
            pass
        
        logout(request)
        
        # Redirect to home page for frontend requests
        if request.META.get('HTTP_ACCEPT', '').find('text/html') != -1:
            return redirect('home')
        
        return Response({'message': 'Successfully logged out.'})


# Alias admin views for URL routing
AdminUserListView = AdminUserListView
AdminConsultationListView = AdminConsultationListView
AdminStatisticsView = AdminStatisticsView
AdminUpdateUserRoleView = AdminUpdateUserRoleView
