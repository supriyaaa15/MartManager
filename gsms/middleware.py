# In middleware.py
from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.contrib import messages

class RoleBasedAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code executed before the view
        path = request.path_info
        
        # Skip middleware for authentication paths
        auth_paths = [reverse('login'), reverse('employee_login'), reverse('admin_login'), 
                     reverse('logout'), reverse('homepage')]
        if path in auth_paths:
            return self.get_response(request)
        
        # Check if user is authenticated before accessing user attributes
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            # Redirect to login if not authenticated
            return redirect('login')
        
        # Now it's safe to access request.user
        user = request.user
        
        # Define path permissions
        admin_only_paths = ['/admin/', '/register/', '/users/', '/suppliers/','/employees/']
        
        # Check permissions
        if user.role != 'Admin' and any(path.startswith(admin_path) for admin_path in admin_only_paths):
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard')
            
        response = self.get_response(request)
        return response