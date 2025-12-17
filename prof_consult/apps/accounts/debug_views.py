"""
Simple test view to replace consultations_list temporarily for debugging.
Use this to isolate the issue.
"""
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from apps.consultations.models import Consultation
from apps.accounts.models import Role

@login_required
def consultations_list_debug(request):
    """
    Debug version of consultations_list that provides detailed error information.
    """
    debug_info = {
        'user_authenticated': request.user.is_authenticated,
        'user_email': request.user.email if request.user.is_authenticated else None,
        'user_role': request.user.role if hasattr(request.user, 'role') else None,
        'errors': []
    }
    
    try:
        # Step 1: Check user
        if not request.user.is_authenticated:
            debug_info['errors'].append('User not authenticated')
            return JsonResponse(debug_info, status=403)
        
        # Step 2: Check user role
        if not hasattr(request.user, 'role'):
            debug_info['errors'].append('User has no role attribute')
            return JsonResponse(debug_info, status=500)
        
        # Step 3: Build queryset
        user = request.user
        if user.role == Role.STUDENT:
            base_qs = Consultation.objects.filter(student=user)
            debug_info['query_type'] = 'student'
        elif user.role == Role.PROFESSOR:
            base_qs = Consultation.objects.filter(professor=user)
            debug_info['query_type'] = 'professor'
        else:
            base_qs = Consultation.objects.all()
            debug_info['query_type'] = 'admin'
        
        # Step 4: Count consultations
        count = base_qs.count()
        debug_info['consultation_count'] = count
        
        # Step 5: Get consultations with select_related
        consultations = base_qs.select_related('student', 'professor')[:10]
        debug_info['fetched_count'] = len(list(consultations))
        
        # Step 6: Try to render template
        context = {
            'consultations': consultations,
            'status_filter': 'upcoming',
        }
        
        try:
            return render(request, 'consultations.html', context)
        except Exception as template_error:
            debug_info['errors'].append(f'Template error: {str(template_error)}')
            debug_info['template_error_type'] = type(template_error).__name__
            import traceback
            debug_info['template_traceback'] = traceback.format_exc()
            return JsonResponse(debug_info, status=500)
        
    except Exception as e:
        debug_info['errors'].append(f'General error: {str(e)}')
        debug_info['error_type'] = type(e).__name__
        import traceback
        debug_info['traceback'] = traceback.format_exc()
        return JsonResponse(debug_info, status=500)


def simple_test(request):
    """
    Simplest possible view to test if Django is working at all.
    """
    return HttpResponse("<h1>Django is working!</h1><p>If you see this, the basic Django setup is OK.</p>")
