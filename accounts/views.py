import json
import random, sys
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect,get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from datetime import date, datetime
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile
import base64
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Count
from django.db.models import Max
#For Admin
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import login
from django.contrib.auth import update_session_auth_hash
from .forms import ProductForm,ReviewForm
from .models import User,Product,Wishlist,Category,Blog,Bidding,Review
from django.utils import timezone
from datetime import timedelta
import json
from django.db.models import Q


#For edit profile
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.contrib.auth import update_session_auth_hash

from .forms import RegistrationForm, EmailAuthenticationForm, PasswordResetRequestForm,CategoryForm,SetNewPasswordForm, UserProfileEditForm, CustomPasswordChangeForm,ContactForm,CustomPasswordForm,BlogForm,BiddingForm  
    #admin csv download
# In your_app/views.py
# ... (your existing imports)
import csv
from django.http import HttpResponse # Ensure this is imported


User = get_user_model()


def home(request): 
    products = Product.objects.all()
    categories = Category.objects.annotate(product_count=Count('product')).order_by('id')[:7]
    blogs = Blog.objects.all().order_by('-created_at')
    for product in products:
            bids = Bidding.objects.filter(product=product).order_by('-bid_amount')
            product.highest_bid = bids.first()
            product.winner = product.highest_bid.user if product.highest_bid else None
            product.is_sold = product.highest_bid is not None
    

    now = timezone.now()
    has_live_products = products.filter(
        auction_start_date_time__lte=now,
        auction_end_date_time__gte=now
    ).exists()
 
    has_upcoming_products = products.filter(
        auction_start_date_time__gt=now
    ).exists()
            
    context ={
        'products':products,
        'categories':categories,
        'blogs':blogs,
        'has_live_products': has_live_products,
        'has_upcoming_products': has_upcoming_products,
    }
    return render(request, "index.html",context)

def about(request): 
    return render(request, "about.html")

def blog(request,pk):
    blog = get_object_or_404(Blog, pk=pk) 
    return render(request, "blog.html",{'blog':blog})

def category(request): 
    categories = Category.objects.annotate(product_count=Count('product')).order_by('id')
    return render(request, "category.html",{'categories':categories})

def contact(request): 
    return render(request, "contact.html")

def seller_list(request): 
    sellers = User.objects.filter(account_type='Seller', is_active=True) 
    context = {
        'sellers': sellers
    }
    return render(request, "seller_list.html", context)

def seller_details(request, pk):
    seller  = get_object_or_404(User, pk=pk, account_type='Seller')
    products = seller.seller_products.all()
    s_cnt = products.count()
    
    context = {
        'seller': seller,
        's_cnt':s_cnt,
        'products': products, 
    }
    return render(request, "seller_details.html", context)

def how_to_sell(request): 
    return render(request, "how-to-sell.html")

def how_to_bid(request): 
    return render(request, "how-to-buy.html")

def faqs(request): 
    return render(request, "faq.html")

def error(request): 
    return render(request, "error.html")

def privacy_policy(request): 
    return render(request, "privacy-policy.html")

def support_center(request): 
    return render(request, "support-center.html")

def terms_condition(request): 
    return render(request, "terms-condition.html")

def password_reset(request): 
    return render(request,"dashboard-change-password.html")

def help_support(request): 
    return render(request,"dashboard-help-and-support.html")

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            
            messages.success(request, 'Thank you! Your message has been submitted successfully.')
            return redirect('contact') 
    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form})

def register_view(request):
    form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def validate_step1(request):
    if request.method == 'POST':
        # Check for existing inactive user with this email and clean it up first
        email = request.POST.get('email')
        User.objects.filter(email__iexact=email, is_active=False).delete()

        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            cleaned_data = form.cleaned_data

            # Store image in session if it exists, converting it to base64
            if 'image' in request.FILES:
                image_file = request.FILES['image']
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
                request.session['registration_image'] = {
                    'name': image_file.name,
                    'content': encoded_image,
                    'content_type': image_file.content_type,
                }
                # Remove from cleaned_data as it's handled separately
                cleaned_data.pop('image')
            
            # Convert date objects to string for session serialization
            if isinstance(cleaned_data.get('date_of_birth'), date):
                cleaned_data['date_of_birth'] = cleaned_data['date_of_birth'].isoformat()

            # Passwords are handled in step 3, so remove them from step 1 data
            cleaned_data.pop('password', None)
            cleaned_data.pop('confirm_password', None)

            request.session['registration_data'] = cleaned_data
            request.session.set_expiry(600)  # Session expires in 10 minutes

            otp = random.randint(100000, 999999)
            request.session['registration_otp'] = otp

            send_mail(
                'Verify your Account',
                f'Your OTP for registration is: {otp}',
                settings.DEFAULT_FROM_EMAIL, [cleaned_data['email']], fail_silently=False,
            )
            return JsonResponse({'success': True})
        else:
            serializable_errors = {}
            for field, error_list in form.errors.items():
                serializable_errors[field] = [str(error) for error in error_list]

            return JsonResponse({'success': False, 'errors': serializable_errors})

    return JsonResponse({'success': False, 'errors': 'Invalid request method'})

def verify_otp(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        entered_otp = data.get('otp')
        stored_otp = request.session.get('registration_otp')

        if entered_otp and stored_otp and int(entered_otp) == stored_otp:
            request.session['otp_verified'] = True
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': {'otp': 'Invalid OTP. Please try again.'}})
    return JsonResponse({'success': False, 'errors': 'Invalid request method'})

def resend_otp(request):
    if request.method == 'POST':
        # Retrieve email from existing session data, not a pre_registered_user_id
        registration_data = request.session.get('registration_data')
        if not registration_data or not registration_data.get('email'):
            return JsonResponse({'success': False, 'message': 'Registration session data not found.'})

        user_email = registration_data['email']
        try:
            otp = random.randint(100000, 999999)
            request.session['registration_otp'] = otp
            send_mail(
                'Your New Verification Code',
                f'Your new OTP is: {otp}',
                settings.DEFAULT_FROM_EMAIL, [user_email], fail_silently=False,
            )
            return JsonResponse({'success': True, 'message': 'A new OTP has been sent.'})
        except Exception as e:
            print(f"Error resending OTP: {e}", file=sys.stderr)
            return JsonResponse({'success': False, 'message': 'Could not resend OTP due to an internal error.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def set_password(request):
    if request.method == 'POST' and request.session.get('otp_verified'):
        registration_data = request.session.get('registration_data')
        if not registration_data:
            return JsonResponse({'success': False, 'errors': {'non_field_errors': 'Session expired. Please start over.'}})

        data = json.loads(request.body)
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        # Basic password validation (already handled by form.is_valid() if using form)
        if not (password and confirm_password and password == confirm_password and len(password) >= 8):
            return JsonResponse({'success': False, 'errors': {'confirm_password': 'Passwords do not match or are too short (min 8 characters).'}})

        try:
            # Create user object without saving yet
            # We use **registration_data to unpack the dictionary into keyword arguments
            # Ensure date_of_birth is converted back to date object if stored as string
            if 'date_of_birth' in registration_data:
                registration_data['date_of_birth'] = date.fromisoformat(registration_data['date_of_birth'])

            user = User(**registration_data)
            user.set_password(password)
            user.is_active = True # User is active after successful registration
            user.save()

            # Handle profile image if it was uploaded
            registration_image = request.session.get('registration_image')
            if registration_image:
                image_content = base64.b64decode(registration_image['content'])
                user.image.save(
                    registration_image['name'],
                    ContentFile(image_content, name=registration_image['name'])
                )

            # Clean up all session data related to registration
            for key in list(request.session.keys()):
                if key.startswith('registration_') or key in ['registration_data', 'otp_verified', 'registration_image']:
                    del request.session[key]

            messages.success(request, 'Account created successfully! You can now log in.')
            return JsonResponse({'success': True}) # Send redirect URL
        except Exception as e:
            print(f"Error creating user: {e}", file=sys.stderr)
            return JsonResponse({'success': False, 'errors': {'non_field_errors': f'An error occurred during account creation: {e}'}})
    return JsonResponse({'success': False, 'errors': 'Invalid request or OTP not verified.'})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.email.lower() == 'sujalzadafiya330@gmail.com':
                return redirect('dashboard-admin')
            else:
                return redirect('home')
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = EmailAuthenticationForm()

    return render(request, 'login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')

def password_reset_request_view(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid(): 
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email__iexact=email)
                otp = random.randint(100000, 999999)
                request.session['reset_otp'] = otp
                request.session['reset_email'] = user.email
                send_mail('Password Reset Request', f'Your OTP to reset your password is: {otp}',
                         settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
                messages.info(request, 'An OTP has been sent to your email.')
                return redirect('password_reset_confirm')
            except User.DoesNotExist:
                messages.error(request, 'No user is registered with this email address.')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'password_reset_request.html', {'form': form})

def password_reset_confirm_view(request):
    reset_email = request.session.get('reset_email')
    if not reset_email:
        messages.error(request, 'Session expired. Please request a new password reset.')
        return redirect('password_reset_request')
    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        entered_otp = request.POST.get('otp')
        stored_otp = request.session.get('reset_otp')
        if entered_otp and stored_otp and int(entered_otp) == stored_otp:
            if form.is_valid():
                user = User.objects.get(email=reset_email)
                user.set_password(form.cleaned_data['password'])
                user.save()
                del request.session['reset_otp']
                del request.session['reset_email']
                messages.success(request, 'Password has been reset successfully. Please log in.')
                return redirect('login')
        else:
            messages.error(request, 'The OTP you entered is incorrect.')
    else:
        form = SetNewPasswordForm()
    return render(request, 'password_reset_confirm.html', {'form': form})


@require_GET
def instant_search(request):
   
    query = request.GET.get('q', '').strip()
    payload = {
        'products': [],
        'categories': [],
        'blogs': [],
    }

    if len(query) < 2:
        return JsonResponse(payload)

    # Limit results to keep response light
    limit = 5

    product_matches = Product.objects.filter(
        Q(product_name__icontains=query) |
        Q(sub_description__icontains=query) |
        Q(product_description__icontains=query)
    ).order_by('-auction_start_date_time')[:limit]

    category_matches = Category.objects.filter(
        Q(name__icontains=query)
    ).order_by('name')[:limit]

    blog_matches = Blog.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query)
    ).order_by('-created_at')[:limit]

    payload['products'] = [
        {
            'title': product.product_name,
            'url': reverse('auction-details', args=[product.id])
        }
        for product in product_matches
    ]

    payload['categories'] = [
        {
            'title': category.name,
            'url': reverse('category_details', args=[category.id])
        }
        for category in category_matches
    ]

    payload['blogs'] = [
        {
            'title': blog.title,
            'url': reverse('blog', args=[blog.id])
        }
        for blog in blog_matches
    ]

    return JsonResponse(payload)


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.email.lower() == 'sujalzadafiya330@gmail.com':
            return view_func(request, *args, **kwargs)
        else:
            return redirect('login') 
    return wrapper

def auction(request):
    products = Product.objects.all().order_by('-auction_start_date_time')
    for product in products:
        bids = Bidding.objects.filter(product=product).order_by('-bid_amount')
        product.highest_bid = bids.first()
        product.winner = product.highest_bid.user if product.highest_bid else None
        product.is_sold = product.highest_bid is not None

    context = {
        'products': products,
    }
    return render(request, "auction.html", context)

@login_required
def auc_details(request, pk):
    product = get_object_or_404(Product, pk=pk)
    reviews = product.reviews.all().order_by('-created_at')
    review_count = reviews.count()
    review_form = ReviewForm()  # Initialize the form
    bids = Bidding.objects.filter(product=product).order_by('-bid_amount')

    highest_bid = bids.first()
    winner = highest_bid.user if highest_bid else None
    if request.method == 'POST':
        form_data = ReviewForm(request.POST)
        if form_data.is_valid():
            new_review = form_data.save(commit=False)
            new_review.product = product

            new_review.user = request.user

            new_review.save()
            messages.success(request, 'Your review was submitted successfully!')
            return redirect('auction-details', pk=pk)
        else:
            review_form = form_data

    context = {
        'product': product,
        'reviews': reviews,
        'review_form': review_form,
        'review_count': review_count,
        'MEDIA_URL': settings.MEDIA_URL,
        'bids':bids,
        'highest_bid': highest_bid,
        'winner': winner,
    }
    
    return render(request, 'auction-details.html', context)

@login_required
def category_details(request, pk):
    category = get_object_or_404(Category, pk=pk)
    products = Product.objects.filter(category=category)

    context = {
        'category':category,
        'products':products,
    }
    return render(request, 'category_details.html', context )

@login_required
def toggle_wishlist(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        
        if wishlist.products.filter(id=product.id).exists():
            wishlist.products.remove(product)
            status = 'removed'
            message = 'Product removed from your wishlist.'
        else:
            wishlist.products.add(product)
            status = 'added'
            message = 'Product added to your wishlist.'
            
        return JsonResponse({'status': status, 'message': message})

    except Product.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Product not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred.'}, status=500)

@login_required
def user_wishlist_products(request):
    """
    Displays the user's wishlist page.
    """
    products = []
    try:
        wishlist = request.user.wishlist
        products = wishlist.products.all()
        for product in products:
            bids = Bidding.objects.filter(product=product).order_by('-bid_amount')
            product.highest_bid = bids.first()
            product.winner = product.highest_bid.user if product.highest_bid else None
            product.is_sold = product.highest_bid is not None
            
    except Wishlist.DoesNotExist:
        pass

    context = {
        'wishlist_products': products
    }
    return render(request, 'wishlist.html', context)


# Seller and bidder profile details

def dash_board(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user

    seller_products = []
    s_cnt = sold_cnt = unsold_cnt = 0
    sold_products = []

    if user.account_type == 'Seller':
        seller_products = user.seller_products.all()
        s_cnt = seller_products.count()

        # Add highest bid info to each product
        for product in seller_products:
            bids = Bidding.objects.filter(product=product).order_by('-bid_amount')
            highest_bid = bids.first()
            product.highest_bid = highest_bid  # attach dynamically
            product.is_sold = bool(highest_bid)  # True if product has any bids

            if product.is_sold:
                sold_products.append(product)

        sold_cnt = len(sold_products)
        unsold_cnt = s_cnt - sold_cnt

    # ------------------------------
    # Buyer part (user’s own bids)
    # ------------------------------
    latest_bids = (
        Bidding.objects.filter(user=user)
        .select_related('product')
        .order_by('product', '-bid_time')
    )

    unique_latest_bids = {}
    for bid in latest_bids:
        if bid.product_id not in unique_latest_bids:
            unique_latest_bids[bid.product_id] = bid

    latest_user_bids = list(unique_latest_bids.values())

    # Mark winning bids
    winning_bids = []
    for bid in latest_user_bids:
        highest_bid = Bidding.objects.filter(product=bid.product).aggregate(Max('bid_amount'))['bid_amount__max']
        if bid.bid_amount == highest_bid:
            winning_bids.append(bid)

    # Stats
    total_bids = Bidding.objects.filter(user=user).count()
    attended_auctions_count = len(latest_user_bids)
    won_auctions_count = len(winning_bids)
    losing_auctions_count = attended_auctions_count - won_auctions_count

    paginator = Paginator(latest_user_bids, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'user': user,
        'page_obj': page_obj,
        'winning_bids': winning_bids,
        'total_bids': total_bids,
        'attended_auctions_count': attended_auctions_count,
        'won_auctions_count': won_auctions_count,
        'losing_auctions_count': losing_auctions_count,

        # Seller-specific
        'products': seller_products,
        's_cnt': s_cnt,
        'sold_cnt': sold_cnt,
        'unsold_cnt': unsold_cnt,
        'sold_products': sold_products,
        'now': timezone.now(),
    }

    return render(request, 'dashboard.html', context)

def user_auction(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user

    if user.account_type == 'Seller':
        # Get seller's products
        seller_products = Product.objects.filter(seller=user).order_by('-auction_start_date_time')
        
        # Add auction status and highest bid info to each product
        now = timezone.now()
        for product in seller_products:
            bids = Bidding.objects.filter(product=product).order_by('-bid_amount')
            product.highest_bid = bids.first()
            product.is_sold = bool(product.highest_bid)
            # Determine auction status
            if product.auction_start_date_time <= now <= product.auction_end_date_time:
                product.status_display = "live"
            elif now < product.auction_start_date_time:
                product.status_display = "upcoming"
            else:
                product.status_display = "closed"
        
        if request.method == 'POST':
            form = ProductForm(request.POST, request.FILES)
            if form.is_valid():
                product_instance = form.save(commit=False)
                product_instance.seller = user

                gallery_files = request.FILES.getlist('gallery_images')
                gallery_paths = []
                for file in gallery_files[:5]:
                    saved_path = default_storage.save(f"products/gallery/{file.name}", file)
                    gallery_paths.append(saved_path)

                product_instance.gallery_images = gallery_paths
                product_instance.save()
                return redirect('user_auction')
        else:
            form = ProductForm()
        return render(request, "dashboard-my-auction.html", {
            'form': form,
            'seller_products': seller_products
        })

    # For bidder users (unchanged)
    latest_user_bids = (
        Bidding.objects
        .filter(user=user)
        .values('product')
        .annotate(max_bid=Max('bid_amount'))
    )

    winning_bids = []
    losing_bids = []

    for entry in latest_user_bids:
        product_id = entry['product']
        user_highest_bid = entry['max_bid']
        user_bid = Bidding.objects.filter(user=user, product_id=product_id, bid_amount=user_highest_bid).first()
        if not user_bid:
            continue
        product = user_bid.product
        highest_bid = product.bids.order_by('-bid_amount').first()
        if highest_bid and highest_bid.user == user:
            winning_bids.append(user_bid)
        else:
            losing_bids.append(user_bid)

    return render(request, "dashboard-my-auction.html", {
        'winning_bids': winning_bids,
        'losing_bids': losing_bids
    })

def edit_profile_view(request):
    form = UserProfileEditForm() 
    return render(request,"dashboard-edit-profile.html",{'form':form})

@login_required
def edit_profile(request):
    user = request.user  

    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('edit_profile') 
    else:
        form = UserProfileEditForm(instance=user)

    return render(request, 'dashboard-edit-profile.html', {'form': form, 'user': user})
    
@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordForm(user=request.user, data=request.POST)
        
        if form.is_valid():
            user = form.save()
            
            update_session_auth_hash(request, user)
            
            messages.success(request, 'Your password has been successfully changed!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:

        form = CustomPasswordForm(user=request.user)
        
    return render(request, 'dashboard-change-password.html', {'form': form})


def add_blog(request):
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = BlogForm()
    return render(request, 'Admin/add_blog.html', {'form': form})

def place_bid(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to place a bid.")
            return redirect('login')

        bid_amount = request.POST.get('bid_amount')
        if not bid_amount:
            messages.error(request, "Please enter a bid amount.")
            return redirect('auction-details', pk=pk)

        try:
            bid_amount = float(bid_amount)
            new_bid = Bidding.objects.create(
                user=request.user,
                product=product,
                bid_amount=bid_amount
            )
            messages.success(request, f"You placed a bid of ₹{bid_amount}")
        except Exception as e:
            messages.error(request, str(e))

    return redirect('auction-details', pk=pk)








@admin_required
def dashboardAdmin(request):
    # Get statistics
    total_bidders = User.objects.filter(account_type='Bidder').count()
    total_sellers = User.objects.filter(account_type='Seller').count()
    total_categories = Category.objects.count()
    total_products = Product.objects.count()
    
    # Get products data for chart (last 6 months)
    
    
    # Get all products for last 6 months
    now = timezone.now()
    six_months_ago = now - timedelta(days=180)
    all_products = Product.objects.filter(
        auction_start_date_time__gte=six_months_ago
    )
    
    # Group products by month
    products_by_month_dict = {}
    for product in all_products:
        month_key = product.auction_start_date_time.strftime('%Y-%m')
        products_by_month_dict[month_key] = products_by_month_dict.get(month_key, 0) + 1
    
    # Generate last 6 months labels and data
    months_list = []
    product_counts_list = []
    
    # Use a more reliable month calculation
    current_date = now.date()
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    for i in range(5, -1, -1):  # Last 6 months: 5 months ago to current
        # Calculate months ago
        target_month = current_date.month - i
        target_year = current_date.year
        
        # Handle year rollover
        while target_month < 1:
            target_month += 12
            target_year -= 1
        while target_month > 12:
            target_month -= 12
            target_year += 1
        
        year_month = f"{target_year}-{target_month:02d}"
        months_list.append(month_names[target_month - 1])
        product_counts_list.append(products_by_month_dict.get(year_month, 0))
    
    context = {
        'total_bidders': total_bidders,
        'total_sellers': total_sellers,
        'total_categories': total_categories,
        'total_products': total_products,
        'months_json': json.dumps(months_list),
        'product_counts_json': json.dumps(product_counts_list),
    }
    return render(request, 'Admin/dashbord_admin.html', context)


@admin_required
def adminManageProduct(request): 

    products = Product.objects.all().order_by('-id')
    
    context = {
        'products': products,
    }
    return render(request, 'Admin/product/manage_product.html', context)

def admin_product_form(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            # Handle gallery images upload (append)
            gallery_files = request.FILES.getlist('gallery_images_upload')
            if gallery_files:
                saved_paths = product.gallery_images or []
                for f in gallery_files:
                    path = default_storage.save(f"products/gallery/{f.name}", f)
                    saved_paths.append(path)
                product.gallery_images = saved_paths
                product.save(update_fields=['gallery_images'])
            return JsonResponse({'ok': True})
        return render(request, 'Admin/product/_product_form.html', {'form': form})
    form = ProductForm()
    return render(request, 'Admin/product/_product_form.html', {'form': form})

def admin_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            # Handle gallery images upload (append)
            gallery_files = request.FILES.getlist('gallery_images_upload')
            if gallery_files:
                saved_paths = product.gallery_images or []
                for f in gallery_files:
                    path = default_storage.save(f"products/gallery/{f.name}", f)
                    saved_paths.append(path)
                product.gallery_images = saved_paths
                product.save(update_fields=['gallery_images'])
            return JsonResponse({'ok': True})
        return render(request, 'Admin/product/_product_form.html', {'form': form})
    form = ProductForm(instance=product)
    return render(request, 'Admin/product/_product_form.html', {'form': form})

def deleteProduct(request, product_id):
    # This is a security measure: only allow POST requests to delete
    if request.method != 'POST':
        messages.error(request, 'Invalid method.')
        return redirect('admin-manage-product')

    # Fetch the specific product by its ID, or return a 404 error if not found
    product_to_delete = get_object_or_404(Product, id=product_id)
    
    # Get the product name before deleting it to use in the message
    product_name = product_to_delete.product_name
    
    # Delete the product from the database
    product_to_delete.delete()
    
    # Create a success message to inform the admin
    messages.success(request, f'Product "{product_name}" has been deleted successfully!')
    
    # Redirect back to the product list page
    return redirect('admin-manage-product')

def adminManageCategory(request):
    # Handle the form submission (POST request)
    if request.method == 'POST':
        # Include request.FILES for image uploads
        form = CategoryForm(request.POST, request.FILES) 
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully!')
            # Redirect to the same page to prevent re-submission and show the new list
            return redirect('admin-manage-category') 
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # For a GET request, just create an empty form
        form = CategoryForm()

    # For both GET requests and failed POST requests, fetch all categories to display in the table
    categories = Category.objects.annotate(product_count=Count('product')).order_by('id')
    
    context = {
        'form': form,
        'categories': categories
    }
    return render(request, 'Admin/category/manage_category.html', context)

def deleteCategory(request, category_id):
# Security: Only allow POST requests for deletion
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('admin-manage-category')

    # Fetch the category object or return a 404 error
    category_to_delete = get_object_or_404(Category, id=category_id)

    # *** CRITICAL SAFETY CHECK ***
    # Check if any products are still using this category
    if category_to_delete.product_set.count() > 0:
        messages.error(request, f'Cannot delete category "{category_to_delete.name}" because it still contains products. Please re-assign them first.')
        return redirect('admin-manage-category')

    # If the check passes, proceed with deletion
    category_name = category_to_delete.name
    category_to_delete.delete()
    
    messages.success(request, f'Category "{category_name}" has been deleted successfully!')
    
    # Redirect back to the category list page
    return redirect('admin-manage-category')

def admin_category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            return JsonResponse({'ok': True})
        return render(request, 'Admin/category/_category_form.html', {'form': form})
    form = CategoryForm(instance=category)
    return render(request, 'Admin/category/_category_form.html', {'form': form})

def adminManageUsers(request):
    sellers = User.objects.filter(account_type='Seller').order_by('-id')
    bidders = User.objects.filter(account_type='Bidder').order_by('-id')
    context = { 'sellers': sellers, 'bidders': bidders }
    return render(request, 'Admin/users/manage_user.html', context)

def admin_user_new(request):
    from .forms import AdminUserForm
    if request.method == 'POST':
        form = AdminUserForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            if form.cleaned_data.get('password'):
                user.set_password(form.cleaned_data['password'])
                user.save(update_fields=['password'])
            return JsonResponse({'ok': True})
        return render(request, 'Admin/users/_user_form.html', {'form': form})
    form = AdminUserForm()
    return render(request, 'Admin/users/_user_form.html', {'form': form})

def admin_user_edit(request, pk):
    from .forms import AdminUserForm
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = AdminUserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save()
            if form.cleaned_data.get('password'):
                user.set_password(form.cleaned_data['password'])
                user.save(update_fields=['password'])
            return JsonResponse({'ok': True})
        return render(request, 'Admin/users/_user_form.html', {'form': form})
    form = AdminUserForm(instance=user)
    return render(request, 'Admin/users/_user_form.html', {'form': form})

def admin_user_delete(request, pk):
    if request.method != 'POST':
        return redirect('admin-manage-users')
    user = get_object_or_404(User, pk=pk)
    user.delete()
    messages.success(request, 'User deleted successfully')
    return redirect('admin-manage-users')

@admin_required
def adminManageReview(request):
    # Get all reviews with product information
    reviews = Review.objects.all().select_related('product', 'user').order_by('-created_at')
    
    context = {
        'reviews': reviews,
    }
    return render(request, 'Admin/review/manage_review.html', context)

@admin_required
def deleteReview(request, review_id):
    # Security: Only allow POST requests for deletion
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('admin-manage-review')
    
    # Fetch the review object or return a 404 error
    review_to_delete = get_object_or_404(Review, id=review_id)
    
    # Store product name for message
    product_name = review_to_delete.product.product_name
    
    # Delete the review
    review_to_delete.delete()
    
    messages.success(request, f'Review for "{product_name}" has been deleted successfully!')
    
    # Redirect back to the review list page
    return redirect('admin-manage-review')



@admin_required
def adminManageBlog(request):
    # Get all blogs with category information
    blogs = Blog.objects.all().select_related('category').order_by('-created_at')

    context = {
        'blogs': blogs,
    }
    return render(request, 'Admin/blog/manage_blog.html', context)

@admin_required
def deleteBlog(request, blog_id):
    # Security: Only allow POST requests for deletion
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('admin-manage-blog')

    # Fetch the blog object or return a 404 error
    blog_to_delete = get_object_or_404(Blog, id=blog_id)

    title = blog_to_delete.title

    # Delete the blog (and its image file via storage backend)
    blog_to_delete.delete()

    messages.success(request, f'Blog "{title}" has been deleted successfully!')

    # Redirect back to the blog list page
    return redirect('admin-manage-blog')


# ... (your existing views)

@admin_required 
def export_products_csv_view(request):
    """
    Exports all products to a CSV file.
    """
    
    # 1. Prepare the CSV response
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="all_auction_products.csv"'},
    )
    
    # 2. Setup CSV writer
    writer = csv.writer(response)
    
    # 3. Define fields and headers
    header_labels = [
        'ID', 
        'Product Name', 
        'Start Price', 
        'Current Bid', 
        'Auction Start Time', 
        'Auction End Time', 
        'Category', 
        'Seller Email', 
        'Status'
    ]
    writer.writerow(header_labels)
    
    # 4. Fetch data (prefetching FKs for performance)
    products = Product.objects.all().select_related('category', 'seller')
    
    # 5. Write data rows
    for product in products:
        row = []
        
        # Manually assemble the row based on the desired order
        row.append(str(product.id))
        row.append(product.product_name)
        row.append(str(product.start_price))
        row.append(str(product.current_bid))
        
        # Format datetimes
        row.append(product.auction_start_date_time.strftime('%Y-%m-%d %H:%M:%S') if product.auction_start_date_time else '')
        row.append(product.auction_end_date_time.strftime('%Y-%m-%d %H:%M:%S') if product.auction_end_date_time else '')
        
        # Foreign Key values
        row.append(product.category.name if product.category else 'N/A')
        row.append(product.seller.email if product.seller else 'N/A')
        
        # Custom method value
        row.append(product.auction_status())
            
        writer.writerow(row)

    return response

