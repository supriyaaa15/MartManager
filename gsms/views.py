import os
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import resolve
from .forms import LoginForm, RegisterUserForm
from .models import UserLogin
from django.contrib.auth.decorators import user_passes_test
from .forms import EmployeeRegistrationForm, ProductForm
from .models import Category, Product, Supplier
from django.http import JsonResponse


# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and user.role == 'Admin'

def homepage(request):
    return render(request, 'homepage.html')

def login_user(request):
    # Determine the expected role based on the URL name
    current_url_name = resolve(request.path_info).url_name
    
    # Set default role expectation based on URL
    expected_role = None
    if current_url_name == 'admin_login':
        expected_role = 'Admin'
    elif current_url_name == 'employee_login':
        expected_role = 'Billing_Employee'
    
    # Override with query parameter if present
    role_from_query = request.GET.get('role', '')
    if role_from_query:
        expected_role = role_from_query
    
    initial_data = {'role': expected_role} if expected_role else {}
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    # Check if the user has the correct role when a specific role is expected
                    if expected_role and user.role != expected_role:
                        messages.error(request, f"This account doesn't have {expected_role} privileges.")
                        return render(request, 'employee_login.html', {'form': form, 'selected_role': expected_role})
                    
                    login(request, user)
                    user.last_login_ip = request.META.get('REMOTE_ADDR')
                    user.failed_login_attempts = 0
                    user.save()
                    return redirect('dashboard')
                else:
                    messages.error(request, "Account is inactive.")
            else:
                # Same error handling as before
                try:
                    user = UserLogin.objects.get(username=username)
                    user.failed_login_attempts += 1
                    user.save()
                except UserLogin.DoesNotExist:
                    pass
                messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm(initial=initial_data)
    
    template = 'employee_login.html'
    return render(request, template, {'form': form, 'selected_role': expected_role})

def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')  # Changed from 'employee_login' to 'login'

@user_passes_test(is_admin)  # Only admins can register new users
def register_user(request):
    if request.method == 'POST':
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Additional setup can be done here
            user.save()
            messages.success(request, f"User {user.username} has been created successfully.")
            return redirect('user_list')  # Redirect to user list
    else:
        form = RegisterUserForm()
    
    return render(request, 'register_user.html', {'form': form})

@login_required
def dashboard(request):
    # Different dashboard views based on role
    if request.user.role == 'Admin':
        return render(request, 'admin_dashboard.html')
    else:  # Billing Employee
        return render(request, 'billing_dashboard.html')

@user_passes_test(is_admin)
def user_list(request):
    users = UserLogin.objects.all()
    return render(request, 'user_list.html', {'users': users})

# @user_passes_test(is_admin)  # Only admins can access this page
# def employees(request):
#     # You can add logic here to fetch employees data
#     return render(request, 'employees.html')

@user_passes_test(is_admin)
def employees(request):
    # Fetch all employees from the database
    employees_list = UserLogin.objects.all()
    return render(request, 'employees.html', {'employees': employees_list})

@user_passes_test(is_admin)  # Only admins can register employees
def register_employee(request):
    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            employee = form.save()
            role_display = "Admin" if employee.role == "Admin" else "Billing Employee"
            messages.success(request, f"{role_display} {employee.username} registered successfully.")
            return redirect('employees')  # Redirect to employee list
        else:
            # If form is not valid, display errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = EmployeeRegistrationForm()
    
    return render(request, 'register_employee.html', {'form': form})

# @user_passes_test(is_admin)
# def edit_employee(request, employee_id):
#     employee = UserLogin.objects.get(id=employee_id)
    
#     if request.method == 'POST':
#         form = EmployeeRegistrationForm(request.POST, instance=employee)
#         if form.is_valid():
#             form.save()
#             messages.success(request, f"Employee {employee.username} updated successfully.")
#             return redirect('employees')
#     else:
#         form = EmployeeRegistrationForm(instance=employee)
    
#     return render(request, 'edit_employee.html', {'form': form, 'employee': employee})

@user_passes_test(is_admin)
def edit_employee(request, employee_id):
    try:
        employee = UserLogin.objects.get(id=employee_id)
    except UserLogin.DoesNotExist:
        messages.error(request, "Employee not found.")
        return redirect('employees')
    
    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f"Employee {employee.username} updated successfully.")
            return redirect('employees')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = EmployeeRegistrationForm(instance=employee)
    
    return render(request, 'edit_employee.html', {'form': form, 'employee': employee})

@user_passes_test(is_admin)
def delete_employee(request, employee_id):
    employee = UserLogin.objects.get(id=employee_id)
    
    if request.method == 'POST':
        employee.is_active = False  # Soft delete
        employee.save()
        messages.success(request, f"Employee {employee.username} has been deactivated.")
        return redirect('employees')
    
    return render(request, 'confirm_delete_employee.html', {'employee': employee})

@login_required
def inventory_management(request):
    categories = Category.objects.all()
    products = Product.objects.all()
    suppliers = Supplier.objects.all()
    
    return render(request, 'inventory_management.html', {
        'categories': categories,
        'products': products,
        'suppliers': suppliers
    })

@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            try:
                product = form.save()
                messages.success(request, f'Product "{product.name}" added successfully!')
                return redirect('inventory_management')
            except Exception as e:
                messages.error(request, f'Database error: {str(e)}')
                print(f"Exception when saving product: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error in {field}: {error}')
            print(f"Form validation errors: {form.errors}")
    else:
        form = ProductForm()
    
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    
    return render(request, 'inventory_management.html', {
        'form': form,
        'categories': categories,
        'suppliers': suppliers
    })

@login_required
def edit_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        messages.error(request, "Product not found.")
        return redirect('inventory_management')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Product '{product.name}' updated successfully.")
            return redirect('inventory_management')
    else:
        form = ProductForm(instance=product)
    
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    
    context = {
        'form': form,
        'product': product,
        'categories': categories,
        'suppliers': suppliers,
        'edit_mode': True
    }
    
    return render(request, 'inventory_management.html', context)

@login_required
def delete_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        messages.error(request, "Product not found.")
        return redirect('inventory_management')
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f"Product '{product_name}' deleted successfully.")
    
    return redirect('inventory_management')

@login_required
def add_category(request):
    if request.method == 'POST':
        category_name = request.POST.get('name')
        if category_name:
            category = Category(name=category_name)
            category.save()
            messages.success(request, f"Category '{category_name}' added successfully.")
        else:
            messages.error(request, "Category name cannot be empty.")
    
    return redirect('inventory_management')

@login_required
def edit_category(request, category_id):
    try:
        category = Category.objects.get(category_id=category_id)
    except Category.DoesNotExist:
        messages.error(request, "Category not found.")
        return redirect('inventory_management')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            category.name = name
            category.save()
            messages.success(request, f"Category updated to '{name}' successfully.")
        else:
            messages.error(request, "Category name cannot be empty.")
    
    return redirect('inventory_management')

@login_required
def delete_category(request, category_id):
    try:
        category = Category.objects.get(category_id=category_id)
    except Category.DoesNotExist:
        messages.error(request, "Category not found.")
        return redirect('inventory_management')
    
    # Check if category has products
    if category.products.exists():
        messages.error(request, f"Cannot delete category '{category.name}' as it contains products.")
    else:
        category_name = category.name
        category.delete()
        messages.success(request, f"Category '{category_name}' deleted successfully.")
    
    return redirect('inventory_management')



@login_required
def get_products_by_category(request, category_id):
    try:
        products = Product.objects.filter(category__category_id=category_id)
        product_list = []
        
        for product in products:
            status = "in-stock"
            if product.stock <= 0:
                status = "out-of-stock"
            elif product.stock < 10:
                status = "low-stock"
            
            product_list.append({
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
                'stock': product.stock,
                'status': status,
                'quantity': product.quantity
            })
        
        return JsonResponse({'products': product_list})
    except Exception as e:
        return JsonResponse({'error': f'Failed to fetch products: {str(e)}'}, status=400)