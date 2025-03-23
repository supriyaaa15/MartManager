from django.contrib import admin
from .models import UserLogin, Category, Product, Supplier, Order, OrderItem, Attendance

# Register your models here.
admin.site.register(UserLogin)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Supplier)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Attendance)
