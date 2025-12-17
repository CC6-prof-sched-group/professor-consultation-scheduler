from django.views.generic import TemplateView, ListView, DetailView, View, CreateView, UpdateView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count
from apps.consultations.models import Consultation
from apps.professors.models import ProfessorProfile
from .forms_admin import AdminUserCreationForm, AdminUserChangeForm

User = get_user_model()

class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

class AdminDashboardView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Stats
        context['total_users'] = User.objects.count()
        context['total_students'] = User.objects.filter(role='STUDENT').count()
        context['total_professors'] = User.objects.filter(role='PROFESSOR').count()
        context['total_consultations'] = Consultation.objects.count()
        
        # Recent Activity (Newest users)
        context['recent_users'] = User.objects.order_by('-date_joined')[:5]
        
        # Recent Consultations
        context['recent_consultations'] = Consultation.objects.order_by('-created_at')[:5]
        
        return context

class AdminUserListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = User
    template_name = 'admin_users_list.html'
    context_object_name = 'users'
    paginate_by = 20
    ordering = ['-date_joined']

    def get_queryset(self):
        queryset = super().get_queryset()
        role = self.request.GET.get('role')
        search = self.request.GET.get('search')
        
        if role:
            queryset = queryset.filter(role=role)
        
        if search:
            queryset = queryset.filter(email__icontains=search) | queryset.filter(username__icontains=search)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_role'] = self.request.GET.get('role', '')
        context['search_term'] = self.request.GET.get('search', '')
        return context

class AdminUserActionView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        action = request.POST.get('action')
        
        if action == 'toggle_active':
            user.is_active = not user.is_active
            user.save()
            status = "activated" if user.is_active else "deactivated"
            messages.success(request, f"User {user.email} has been {status}.")
        
        elif action == 'promote_admin':
            user.is_superuser = True
            user.is_staff = True
            user.save()
            messages.success(request, f"User {user.email} is now an Admin.")
            
        elif action == 'demote_admin':
            if user == request.user:
                messages.error(request, "You cannot demote yourself.")
            else:
                user.is_superuser = False
                user.is_staff = False
                user.save()
                messages.success(request, f"User {user.email} is no longer an Admin.")
                
        return redirect('admin_users_list')

class BecomeAdminView(LoginRequiredMixin, View):
    def post(self, request):
        # In a real app, this should be protected by a secret key or disabled in production
        # For this request, we allow it for any logged-in user via the settings page
        
        request.user.is_superuser = True
        request.user.is_staff = True
        request.user.save()
        
        messages.success(request, "You are now an Administrator! Access the dashboard from the navbar.")
        return redirect('profile_settings')

class AdminCreateUserView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = User
    form_class = AdminUserCreationForm
    template_name = 'admin_user_create.html'
    success_url = reverse_lazy('admin_users_list')

    def form_valid(self, form):
        messages.success(self.request, f"User {form.cleaned_data['email']} created successfully.")
        return super().form_valid(form)

class AdminUserUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = User
    form_class = AdminUserChangeForm
    template_name = 'admin_user_edit.html'
    success_url = reverse_lazy('admin_users_list')

    def form_valid(self, form):
        messages.success(self.request, f"User {form.cleaned_data['email']} updated successfully.")
        return super().form_valid(form)
