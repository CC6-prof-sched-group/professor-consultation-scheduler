from django.http import JsonResponse
from django.db import connection


def health_check(request):
    """
    Simple health check endpoint for monitoring services.
    Returns 200 OK if the application and database are responding.
    """
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected'
        }, status=200)
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)
