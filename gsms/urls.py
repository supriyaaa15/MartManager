from django.urls import path
from . import views
from django.shortcuts import render



urlpatterns = [
    path('', views.homepage, name='homepage'),
    
    # General login URL that middleware can use
    path('login/', views.login_user, name='login'),
    
    # Role-specific login URLs
    path('employee-login/', views.login_user, name='employee_login'),
    path('admin-login/', views.login_user, name='admin_login'),
    
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register_user'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('users/', views.user_list, name='user_list'),
    path('employees/', views.employees, name='employees'),
    path('register-employee/', views.register_employee, name='register_employee'),
    path('edit-employee/<int:employee_id>/', views.edit_employee, name='edit_employee'),
    path('delete-employee/<int:employee_id>/', views.delete_employee, name='delete_employee'),
    path('inventory/', views.inventory_management, name='inventory_management'),
    path('add-product/', views.add_product, name='add_product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('add-category/', views.add_category, name='add_category'),
    path('edit-category/<int:category_id>/', views.edit_category, name='edit_category'),
    path('delete-category/<int:category_id>/', views.delete_category, name='delete_category'),
    path('api/products/<int:category_id>/', views.get_products_by_category, name='get_products_by_category'),
    path('api/product/<int:product_id>/', views.get_product, name='get_product'),
    path('api/product/<int:product_id>/update/', views.update_product, name='update_product'),
    path('api/product/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    path('api/products/all/', views.get_all_products, name='get_all_products'),
    path('api/suppliers/<int:supplier_id>/products/', views.get_supplier_products, name='get_supplier_products'),
    path('manage-orders/', views.manage_orders, name='manage_orders'),
    path('api/orders/create/', views.create_order, name='create_order'),
    path('api/orders/<int:order_id>/receive/', views.mark_order_received, name='mark_order_received'),
    path('api/orders/<int:order_id>/delete/', views.delete_order, name='delete_order'),
    path('add_supplier_to_products/', views.add_supplier_to_products, name='add_supplier_to_products'),
    path('add-supplier/', views.add_supplier_view, name='add_supplier'),
    # Add other URLs as needed
]