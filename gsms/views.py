import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import resolve
from .forms import LoginForm, RegisterUserForm
from .models import UserLogin, Order, OrderItem, Category, Product, Supplier, Attendance
from django.contrib.auth.decorators import user_passes_test
from .forms import EmployeeRegistrationForm, ProductForm
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import F
from decimal import Decimal
from django.utils import timezone
from datetime import datetime, date, timedelta

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
    suppliers = Supplier.objects.filter(is_active=True)  # Only get active suppliers
    
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
    suppliers = Supplier.objects.filter(is_active=True)  # Only get active suppliers
    
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
    
@require_http_methods(["GET"])
def get_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        product_data = {
            'id': product.id,
            'name': product.name,
            'category': {
                'id': product.category.category_id,
                'name': product.category.name
            },
            'price': product.price,
            'stock': product.stock,
            'quantity': product.quantity,
            'expiry_date': product.expiry_date.strftime('%Y-%m-%d') if product.expiry_date else None
        }
        return JsonResponse(product_data)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
def update_product(request, product_id):
    try:
        data = json.loads(request.body)
        product = Product.objects.get(id=product_id)
        
        # Update product fields
        product.name = data.get('name', product.name)
        product.price = data.get('price', product.price)
        product.stock = data.get('stock', product.stock)
        product.quantity = data.get('quantity', product.quantity)
        
        # Update category if provided
        if 'category' in data:
            category_id = data['category']
            category = Category.objects.get(category_id=category_id)
            product.category = category
        
        # Update expiry date if provided
        if 'expiry_date' in data and data['expiry_date']:
            product.expiry_date = data['expiry_date']
        
        product.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Product updated successfully'
        })
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    except Category.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Category not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def delete_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        product_name = product.name
        product.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Product "{product_name}" deleted successfully'
        })
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
def get_all_products(request):
    products = Product.objects.all().select_related('category')
    products_data = []
    
    for product in products:
        product_data = {
            'id': product.id,
            'name': product.name,
            'category': {
                'id': product.category.category_id,
                'name': product.category.name
            },
            'quantity': product.quantity,
            'price': float(product.price),
            'stock': product.stock,
            'expiry_date': product.expiry_date.isoformat() if product.expiry_date else None,
            'status': 'out-of-stock' if product.stock == 0 else 'low-stock' if product.stock < 10 else 'in-stock'
        }
        products_data.append(product_data)
    
    return JsonResponse({'products': products_data})

def manage_orders(request):
    # Only get active suppliers
    suppliers = Supplier.objects.filter(is_active=True).prefetch_related('products').all()
    
    # Get pending orders with pagination
    pending_orders = Order.objects.filter(status='pending').order_by('-created_at')
    paginator = Paginator(pending_orders, 10)  # Show 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get completed orders with pagination and date filtering
    completed_orders = Order.objects.filter(status='completed')
    
    # Apply date filters if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        start_datetime = timezone.datetime.strptime(start_date, '%Y-%m-%d')
        start_datetime = timezone.make_aware(start_datetime)
        completed_orders = completed_orders.filter(created_at__gte=start_datetime)
    
    if end_date:
        end_datetime = timezone.datetime.strptime(end_date, '%Y-%m-%d')
        end_datetime = timezone.make_aware(end_datetime)
        end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
        completed_orders = completed_orders.filter(created_at__lte=end_datetime)
    
    completed_orders = completed_orders.order_by('-received_date')
    completed_paginator = Paginator(completed_orders, 10)
    completed_page_number = request.GET.get('completed_page')
    completed_page_obj = completed_paginator.get_page(completed_page_number)
    
    return render(request, 'manageOrders.html', {
        'suppliers': suppliers,
        'pending_orders': page_obj,
        'completed_orders': completed_page_obj
    })

@csrf_exempt
@require_http_methods(["POST"])
def create_order(request):
    try:
        data = json.loads(request.body)
        supplier_id = data.get('supplier_id')
        items = data.get('items', [])
        
        if not supplier_id or not items:
            return JsonResponse({'error': 'Missing required data'}, status=400)
        
        supplier = Supplier.objects.get(id=supplier_id)
        
        # Calculate total amount
        total_amount = Decimal('0.00')
        order_items = []
        
        for item in items:
            product = Product.objects.get(id=item['product_id'])
            quantity = int(item['quantity'])
            price = Decimal(str(item['price']))
            subtotal = price * quantity
            total_amount += subtotal
            
            order_items.append({
                'product': product,
                'quantity': quantity,
                'price': price,
                'subtotal': subtotal
            })
        
        # Apply 20% discount if total exceeds 15000
        discount = Decimal('0.00')
        if total_amount > Decimal('15000.00'):
            discount = total_amount * Decimal('0.20')
            total_amount -= discount
        
        # Create order with transaction
        with transaction.atomic():
            order = Order.objects.create(
                supplier=supplier,
                total_amount=total_amount,
                discount=discount,
                status='pending'
            )
            
            # Create order items
            for item in order_items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity'],
                    price=item['price'],
                    subtotal=item['subtotal']
                )
        
        return JsonResponse({
            'success': True,
            'message': 'Order created successfully',
            'order_id': order.id,
            'total_amount': float(total_amount),
            'discount': float(discount)
        })
        
    except Supplier.DoesNotExist:
        return JsonResponse({'error': 'Supplier not found'}, status=404)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def mark_order_received(request, order_id):
    try:
        with transaction.atomic():
            order = Order.objects.get(id=order_id)
            
            # Update order status
            order.status = 'completed'
            order.received_date = timezone.now()
            order.save()
            
            # Update product stock
            for item in order.items.all():
                product = item.product
                product.stock += item.quantity
                product.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Order marked as received successfully'
            })
            
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_order(request, order_id):
    try:
        with transaction.atomic():
            order = Order.objects.get(id=order_id)
            
            # Only allow deletion of completed orders
            if order.status != 'completed':
                return JsonResponse({
                    'error': 'Only completed orders can be deleted'
                }, status=400)
            
            # Delete the order (this will cascade delete order items)
            order.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Order deleted successfully'
            })
            
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def add_supplier_to_products(supplier_id, product_ids):
    """
    Associates a single supplier with multiple products.
    
    Args:
        supplier_id (int): The ID of the supplier to add
        product_ids (list): A list of product IDs to associate with the supplier
        
    Returns:
        int: The number of products that were processed
    """
    try:
        # Get the supplier
        supplier = Supplier.objects.get(id=supplier_id)
        
        # Get the products
        products = Product.objects.filter(id__in=product_ids)
        
        # Count before adding to know how many products we're processing
        product_count = products.count()
        
        if product_count == 0:
            return 0  # No products found
            
        # Add the supplier to all products in a single operation
        supplier.products.add(*products)
        
        return product_count
        
    except Supplier.DoesNotExist:
        # Handle the case where the supplier doesn't exist
        raise ValueError(f"Supplier with ID {supplier_id} does not exist")
    except Exception as e:
        # Handle other exceptions
        raise e


def add_supplier_view(request):
    # Get all suppliers for the dropdown
    suppliers = Supplier.objects.filter(is_active=True)
    
    # Get all products for the multi-select
    products = Product.objects.all()
    
    if request.method == 'POST':
        # Get the form data
        supplier_id = request.POST.get('supplier')
        product_ids = request.POST.getlist('products')  # getlist() for multiple selections
        
        if not supplier_id or not product_ids:
            messages.error(request, "Please select a supplier and at least one product")
            return render(request, 'add_supplier.html', {'suppliers': suppliers, 'products': products})
        
        try:
            # Wrap in a transaction for safety
            with transaction.atomic():
                supplier = Supplier.objects.get(id=supplier_id)
                selected_products = Product.objects.filter(id__in=product_ids)
                
                # Add the supplier to all selected products
                supplier.products.add(*selected_products)
                
                messages.success(
                    request, 
                    f"Successfully added supplier '{supplier.name}' to {len(product_ids)} products"
                )
                return redirect('product_list')  # Redirect to your product list view
                
        except Supplier.DoesNotExist:
            messages.error(request, "The selected supplier does not exist")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
    
    # For GET requests or if there's an error
    return render(request, 'add_supplier.html', {'suppliers': suppliers, 'products': products})

@require_http_methods(["GET"])
def get_supplier_products(request, supplier_id):
    try:
        supplier = Supplier.objects.get(id=supplier_id)
        products = supplier.products.all()
        
        product_list = []
        for product in products:
            product_list.append({
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
                'quantity': product.quantity,
                'stock': product.stock
            })
        
        return JsonResponse({'products': product_list})
    except Supplier.DoesNotExist:
        return JsonResponse({'error': 'Supplier not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def attendance(request):
    employees = UserLogin.objects.all()
    # Get today's attendance for each employee
    today = timezone.now().date()
    for employee in employees:
        employee.today_attendance = Attendance.objects.filter(employee=employee, date=today).first()
    
    context = {
        'employees': employees
    }
    return render(request, 'attendance.html', context)

@login_required
def mark_attendance(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        employee_id = data.get('employee_id')
        date = data.get('date')
        status = data.get('status')
        
        if not all([employee_id, date, status]):
            return JsonResponse({'success': False, 'message': 'Missing required fields'})
        
        employee = UserLogin.objects.get(id=employee_id)
        attendance_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Update or create attendance record
        attendance, created = Attendance.objects.update_or_create(
            employee=employee,
            date=attendance_date,
            defaults={'status': status}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Attendance marked as {status} for {employee.username}'
        })
        
    except UserLogin.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Employee not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def get_monthly_attendance(request, employee_id, year, month):
    try:
        employee = UserLogin.objects.get(id=employee_id)
        
        # Get all attendance records for the specified month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        attendance_records = Attendance.objects.filter(
            employee=employee,
            date__range=[start_date, end_date]
        )
        
        # Create attendance dictionary
        attendance_dict = {}
        present_count = 0
        absent_count = 0
        
        for record in attendance_records:
            attendance_dict[record.date.day] = record.status
            if record.status == 'present':
                present_count += 1
            else:
                absent_count += 1
        
        return JsonResponse({
            'success': True,
            'attendance': attendance_dict,
            'summary': {
                'present': present_count,
                'absent': absent_count
            }
        })
        
    except UserLogin.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Employee not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def add_supplier(request):
    try:
        data = request.POST
        
        # Validate required fields
        required_fields = ['name', 'email', 'contact', 'address']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'message': f'{field.title()} is required'
                }, status=400)
        
        # Check if a supplier with this email exists (active or inactive)
        existing_supplier = Supplier.objects.filter(email=data.get('email')).first()
        
        if existing_supplier:
            if existing_supplier.is_active:
                return JsonResponse({
                    'success': False,
                    'message': 'A supplier with this email already exists'
                }, status=400)
            else:
                # Reactivate the existing supplier with updated information
                existing_supplier.name = data.get('name')
                existing_supplier.contact = data.get('contact')
                existing_supplier.address = data.get('address')
                existing_supplier.is_active = True
                existing_supplier.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Supplier reactivated successfully',
                    'supplier': {
                        'id': existing_supplier.id,
                        'name': existing_supplier.name,
                        'email': existing_supplier.email,
                        'contact': existing_supplier.contact
                    }
                })
        
        # Create new supplier if no existing supplier found
        supplier = Supplier.objects.create(
            name=data.get('name'),
            email=data.get('email'),
            contact=data.get('contact'),
            address=data.get('address'),
            is_active=True
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Supplier added successfully',
            'supplier': {
                'id': supplier.id,
                'name': supplier.name,
                'email': supplier.email,
                'contact': supplier.contact
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def remove_supplier(request, supplier_id):
    try:
        supplier = get_object_or_404(Supplier, id=supplier_id)
        
        # Check if any products from this supplier have stock
        products_with_stock = Product.objects.filter(suppliers=supplier, stock__gt=0)
        if products_with_stock.exists():
            return JsonResponse({
                'success': False,
                'message': 'Cannot remove supplier. Some products still have stock.'
            }, status=400)
        
        # Remove supplier from all products with zero stock
        products_without_stock = Product.objects.filter(suppliers=supplier, stock=0)
        for product in products_without_stock:
            product.suppliers.remove(supplier)
        
        # Hard delete the supplier instead of soft delete
        supplier.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Supplier removed successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)