from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import AbstractUser

class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Supplier(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)  # Added unique=True
    address = models.TextField()
    contact = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)  # For soft delete
    
    def __str__(self):
        return self.name

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.CharField(max_length=50, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    stock = models.IntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    suppliers = models.ManyToManyField(Supplier, related_name='products')
    
    def __str__(self):
        return self.name

class UserLogin(AbstractUser):
    # id, username, and password are inherited from AbstractUser
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=[
        ('Admin', 'Admin'),
        ('Billing_Employee', 'Billing Employee'),  # Updated from just 'Employee'
    ], default='Admin')
    is_active = models.BooleanField(default=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # Optional additional field
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)  # For security tracking
    failed_login_attempts = models.IntegerField(default=0)  # For security 
    
    # Keep the existing related_name fix
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        related_name='gsms_user_set',
        related_query_name='gsms_user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        related_name='gsms_user_set',
        related_query_name='gsms_user'
    )
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class Transaction(models.Model):
    trans_id = models.AutoField(primary_key=True)
    trans_date = models.DateTimeField(auto_now_add=True)
    total_amt = models.DecimalField(max_digits=12, decimal_places=2)
    pay_method = models.CharField(max_length=50)
    user = models.ForeignKey(UserLogin, on_delete=models.CASCADE, related_name='transactions')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='transactions')
    user_deleted = models.BooleanField(default=False)  # Soft delete flag for user
    supplier_deleted = models.BooleanField(default=False)  # Soft delete flag for supplier
    
    def __str__(self):
        return f"Transaction {self.trans_id} - {self.trans_date}"

class TransactionDetail(models.Model):
    id = models.AutoField(primary_key=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='details')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transaction_details')
    quantity = models.IntegerField(default=0)  # Added default=0
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price per item
    
    def __str__(self):
        return f"Detail for Transaction {self.transaction.trans_id} - {self.product.name}"