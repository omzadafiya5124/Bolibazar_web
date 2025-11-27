    # In accounts/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.db.models import Max
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage


#For Edit profile
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    ACCOUNT_TYPE_CHOICES = (('Bidder', 'Bidder'), ('Seller', 'Seller'))
    
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    mobile_number = models.CharField(max_length=15)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPE_CHOICES)
    image = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username','date_of_birth']

    def __str__(self):
        return self.email
    
class Category(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="category/",null=True, blank=True)

    def __str__(self):
        return self.name
    
    def delete(self, *args, **kwargs):
    # Delete the associated image file from storage before deleting the database record.
        if self.image:
            if default_storage.exists(self.image.name):
                default_storage.delete(self.image.name)
        super().delete(*args, **kwargs)

class Product(models.Model):
    product_name = models.CharField(max_length=200)
    sub_description = models.TextField(default='')
    product_description = models.TextField()
    start_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_bid = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    auction_start_date_time = models.DateTimeField(default=timezone.now)
    auction_end_date_time = models.DateTimeField()

    main_image = models.ImageField(upload_to="products/")
    gallery_images = models.JSONField(default=list, blank=True)

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='seller_products',null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    
    def __str__(self):
        return self.product_name

    # Set current_bid to start_price when a new product is created
    def save(self, *args, **kwargs):
        if not self.id and self.current_bid is None:
            self.current_bid = self.start_price
        super().save(*args, **kwargs)

    # **CRITICAL**: Custom delete method to remove associated files from storage
    def delete(self, *args, **kwargs):
        # First, delete the main image file
        self.main_image.delete(save=False)
        
        # Loop through the JSON list and delete each gallery image file
        for image_path in self.gallery_images:
            if default_storage.exists(image_path):
                default_storage.delete(image_path)

        # Call the original delete method
        super().delete(*args, **kwargs)

    def auction_status(self):
        now = timezone.now()
        if self.auction_start_date_time <= now <= self.auction_end_date_time:
            return "live"
        elif now < self.auction_start_date_time:
            return "upcoming"
        else:
            return "closed"
        
    def countdown_start(self):
        """Return the datetime to start countdown, only if auction has started."""
        now = timezone.now()
        if now >= self.auction_start_date_time and now <= self.auction_end_date_time:
            return self.auction_end_date_time
        return None

    def highest_bid(self):
        return self.bids.order_by('-bid_amount').first()

    def winner(self):
        highest = self.highest_bid()
        if highest:
            return highest.user
        return None

    def delete(self, *args, **kwargs):
    # This line causes the error because default_storage is not defined
        if self.main_image:
            # Check if the file exists before trying to delete it
            if default_storage.exists(self.main_image.name):
                default_storage.delete(self.main_image.name)
        
        # Then, call the superclass's delete method to remove the database record
        super().delete(*args, **kwargs)

      # for print status
    def auction_status(self):
        now = timezone.now()
        if self.auction_start_date_time <= now <= self.auction_end_date_time:
            return "live"       # Used for 'Active' or 'Live' status
        elif now < self.auction_start_date_time:
            return "upcoming"   # Used for 'Pending' or 'Upcoming' status
        else:
            return "closed"

class Wishlist(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    products = models.ManyToManyField(Product, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wishlist of {self.user.username}"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews',null=True, blank=True) 
    message = models.TextField()
    rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Review for {self.product.name} by {self.name}'

#Contect Form
class ContactSubmission(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True) # blank=True makes it optional
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} - {self.email}"  

class Blog(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="blogs")
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to="blogs/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Bidding(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="bids")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    bid_time = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-bid_amount']  # Highest bids first

    def __str__(self):
        return f"{self.user.username} - {self.product.product_name} - {self.bid_amount}"

    def clean(self):
        """Ensure bid is higher than current product price"""
        if self.product.current_bid and self.bid_amount <= self.product.current_bid:
            raise ValidationError("Bid amount must be higher than current bid price.")

    def save(self, *args, **kwargs):
        """Save bid and update current product bid if it's higher"""
        self.clean()
        super().save(*args, **kwargs)

        # Update product's current bid if this is the highest
        highest_bid = Bidding.objects.filter(product=self.product).aggregate(Max('bid_amount'))['bid_amount__max']
        if highest_bid and highest_bid > self.product.current_bid:
            self.product.current_bid = highest_bid
            self.product.save()