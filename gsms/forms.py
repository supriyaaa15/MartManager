from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UserLogin
from .models import Product, Category, Supplier


class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)

class RegisterUserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=UserLogin._meta.get_field('role').choices)
    phone_number = forms.CharField(max_length=15, required=False)
    
    class Meta:
        model = UserLogin
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone_number', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        user.phone_number = self.cleaned_data['phone_number']
        
        if commit:
            user.save()
        return user
    
class EmployeeRegistrationForm(RegisterUserForm):
    """
    Form specifically for employee registration with any additional fields
    or validations that might be needed for employees.
    """
    
    # By default, inherit everything from RegisterUserForm
    # You could add additional fields here if needed
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set a default role but allow selection
        self.fields['role'].initial = 'Billing_Employee'
        
        # You could add additional customizations here
        # For example, making certain fields required for employees
        self.fields['phone_number'].required = True
        
        # Or adding help text to fields
        self.fields['username'].help_text = "This will be used for login"
        self.fields['email'].help_text = "Official email address"



class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'price', 'quantity', 'expiry_date', 'stock', 'suppliers']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'suppliers': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['suppliers'].required = False  # Make the suppliers field optional