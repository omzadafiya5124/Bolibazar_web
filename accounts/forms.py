# In accounts/forms.py

from django import forms
from datetime import date
from django.contrib.auth.forms import AuthenticationForm 
from .models import User
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from .models import Product,Review,ContactSubmission,Category,Blog,Bidding

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactSubmission
        fields = ['name', 'phone', 'email', 'message']


#edit pro
class UserProfileEditForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    image = forms.ImageField(required=False, widget=forms.FileInput)
    gender = forms.ChoiceField(
        choices=User.GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = User
        # --- KEY CHANGE: Remove 'account_type' from this list ---
        fields = [
            'username', 'email', 'mobile_number',
            'date_of_birth', 'gender', 'image'  # 'account_type' has been removed
        ]

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

    # Your clean_username and clean_email methods remain unchanged
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This username is already taken. Please choose a different one.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email


class CustomPasswordForm(PasswordChangeForm):
    old_password = forms.CharField(
        label='Old Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your old password'})
    )
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter a new password'})
    )
    new_password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your new password'})
    )

    class Meta:
        model = User # Assuming your user model is the default
        fields = ('old_password', 'new_password1', 'new_password2')

class CustomPasswordChangeForm(PasswordChangeForm):
    """A styled version of Django's secure password change form."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'placeholder': '********',
                'autocomplete': 'new-password' # Helps prevent browser auto-filling
            })

class RegistrationForm(forms.ModelForm):
    # These fields are defined here to control their order and widgets
    password = forms.CharField(label='Password', widget=forms.PasswordInput, required=False, min_length=8)
    confirm_password = forms.CharField(label='Confirm Password', widget=forms.PasswordInput, required=False)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

   
    class Meta:
        model = User
        fields = ['username', 'email', 'mobile_number', 'date_of_birth', 'gender', 'account_type', 'image']
        
    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        # Ensure we don't validate against an existing inactive user during their own registration
        if User.objects.filter(email__iexact=email, is_active=True).exists():
            raise forms.ValidationError("An active account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data


    def save(self, commit=True):
        # The password is now set in the view, so we just call the parent save method
        user = super().save(commit=commit)
        return user

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email Address", widget=forms.EmailInput(attrs={'autofocus': True}))
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput)

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Your Email Address")

class SetNewPasswordForm(forms.Form):
    password = forms.CharField(label='New Password', widget=forms.PasswordInput)
    confirm_password = forms.CharField(label='Confirm New Password', widget=forms.PasswordInput)

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return confirm_password
    
class ProductForm(forms.ModelForm):
    class MultiFileInput(forms.ClearableFileInput):
        allow_multiple_selected = True

    gallery_images_upload = forms.FileField(
        required=False,
        widget=MultiFileInput(attrs={'class': 'form-control', 'multiple': True})
    )

    class Meta:
        model = Product
        fields = [
            'product_name', 'sub_description', 'product_description', 'start_price',
            'auction_start_date_time', 'auction_end_date_time',
            'category', 'seller', 'main_image',
        ]
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'sub_description': forms.TextInput(attrs={'class': 'form-control'}),
            'product_description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'start_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'auction_start_date_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'auction_end_date_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'seller': forms.Select(attrs={'class': 'form-control'}),
            'main_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit sellers to users with Seller account type
        if 'seller' in self.fields:
            self.fields['seller'].queryset = User.objects.filter(account_type='Seller')


class AdminUserForm(forms.ModelForm):
    password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    inactive = forms.BooleanField(required=False, label='Inactive', widget=forms.CheckboxInput())

    class Meta:
        model = User
        fields = ['username','email','mobile_number','date_of_birth','gender','account_type','image']
        widgets = {
            'username': forms.TextInput(attrs={'class':'form-control'}),
            'email': forms.EmailInput(attrs={'class':'form-control'}),
            'mobile_number': forms.TextInput(attrs={'class':'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type':'date','class':'form-control'}),
            'gender': forms.Select(attrs={'class':'form-control'}),
            'account_type': forms.Select(attrs={'class':'form-control'}),
            'image': forms.FileInput(attrs={'class':'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure the date input cannot select a future date (client-side hint)
        if 'date_of_birth' in self.fields and hasattr(self.fields['date_of_birth'], 'widget'):
            self.fields['date_of_birth'].widget.attrs['max'] = date.today().isoformat()
        # Set inactive initial value from instance.is_active
        instance = kwargs.get('instance')
        if instance is not None:
            self.fields['inactive'].initial = not bool(instance.is_active)

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > date.today():
            raise forms.ValidationError('Date of birth cannot be in the future.')
        return dob

    def save(self, commit=True):
        user = super().save(commit=False)
        # Apply inactive checkbox to is_active
        inactive = self.cleaned_data.get('inactive')
        if inactive is not None:
            user.is_active = not bool(inactive)
        if commit:
            user.save()
        return user

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['message', 'rating']
        widgets = {
            'message': forms.Textarea(attrs={'placeholder': 'Message...'}),
            'rating': forms.HiddenInput(),  # set by JavaScript (e.g. from the star rating)
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'image']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name',
            }),
        }

class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['category', 'title', 'description', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter blog title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Write your blog...'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }

class BiddingForm(forms.ModelForm):
    class Meta:
        model = Bidding
        fields = ['bid_amount']
        widgets = {
            'bid_amount': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '0',
                'step': '1',
                'id': 'bidInput'
            }),
        }











       
