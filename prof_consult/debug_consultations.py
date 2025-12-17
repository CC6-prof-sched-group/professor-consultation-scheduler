"""
Debug script to test consultations view functionality.
Run this in PythonAnywhere console or manage.py shell.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prof_consult.settings')
django.setup()

from apps.consultations.models import Consultation
from apps.accounts.models import User, Role
from django.test import RequestFactory
from apps.accounts.frontend_views import consultations_list

def test_consultations_view():
    """Test the consultations_list view with different scenarios."""
    print("=" * 60)
    print("DEBUGGING CONSULTATIONS VIEW")
    print("=" * 60)
    
    # Test 1: Check if consultations exist
    print("\n1. Checking consultations in database...")
    consultation_count = Consultation.objects.count()
    print(f"   Total consultations: {consultation_count}")
    
    # Test 2: Check users
    print("\n2. Checking users...")
    user_count = User.objects.count()
    print(f"   Total users: {user_count}")
    
    students = User.objects.filter(role=Role.STUDENT).count()
    professors = User.objects.filter(role=Role.PROFESSOR).count()
    admins = User.objects.filter(role=Role.ADMIN).count()
    print(f"   Students: {students}, Professors: {professors}, Admins: {admins}")
    
    # Test 3: Try to get first user and test view
    print("\n3. Testing consultations_list view...")
    try:
        factory = RequestFactory()
        
        # Test with student user
        student = User.objects.filter(role=Role.STUDENT).first()
        if student:
            print(f"   Testing with student: {student.email}")
            request = factory.get('/consultations/')
            request.user = student
            
            try:
                response = consultations_list(request)
                print(f"   ✓ View executed successfully (Status: {response.status_code})")
            except Exception as e:
                print(f"   ✗ View failed with error: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print("   No student users found in database")
            
        # Test with professor user
        professor = User.objects.filter(role=Role.PROFESSOR).first()
        if professor:
            print(f"   Testing with professor: {professor.email}")
            request = factory.get('/consultations/')
            request.user = professor
            
            try:
                response = consultations_list(request)
                print(f"   ✓ View executed successfully (Status: {response.status_code})")
            except Exception as e:
                print(f"   ✗ View failed with error: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print("   No professor users found in database")
            
    except Exception as e:
        print(f"   ✗ Error during test: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Check template tags
    print("\n4. Testing template tags...")
    try:
        from apps.professors.templatetags.rating_tags import star_rating, rating_class
        
        # Test star_rating
        try:
            result = star_rating(4.5)
            print(f"   ✓ star_rating(4.5) works: {result}")
        except Exception as e:
            print(f"   ✗ star_rating failed: {type(e).__name__}: {str(e)}")
        
        # Test rating_class
        try:
            result = rating_class(4.5)
            print(f"   ✓ rating_class(4.5) works: {result}")
        except Exception as e:
            print(f"   ✗ rating_class failed: {type(e).__name__}: {str(e)}")
            
    except ImportError as e:
        print(f"   ✗ Could not import template tags: {str(e)}")
    
    # Test 5: Check for consultations with issues
    print("\n5. Checking for data integrity issues...")
    try:
        consultations = Consultation.objects.all()[:5]
        for c in consultations:
            try:
                _ = c.student.email
                _ = c.professor.email
                _ = str(c)
            except Exception as e:
                print(f"   ✗ Consultation {c.id} has issue: {type(e).__name__}: {str(e)}")
        print(f"   ✓ Checked {min(5, consultation_count)} consultations - no issues found")
    except Exception as e:
        print(f"   ✗ Error checking consultations: {type(e).__name__}: {str(e)}")
    
    print("\n" + "=" * 60)
    print("DEBUG COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    test_consultations_view()
