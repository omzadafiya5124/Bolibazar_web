# in your_app/context_processors.py
# (e.g., accounts/context_processors.py)

from .models import Wishlist,Category,Product
from django.db.models import Count

def user_wishlist_products(request):
    if request.user.is_authenticated:
        try:
            # Get the user's wishlist and fetch only the product IDs.
            # This is very fast and uses minimal memory.
            wishlist = Wishlist.objects.get(user=request.user)
            product_ids = list(wishlist.products.values_list('id', flat=True))
            return {'user_wishlist_products': product_ids}
        except Wishlist.DoesNotExist:
            # If the user has no wishlist yet, return an empty list.
            return {'user_wishlist_products': []}
    
    # For anonymous users, return an empty list.
    return {'user_wishlist_products': []}

def global_categories(request):
    return {
        'categories1' : Category.objects.annotate(product_count=Count('product')).order_by('id')[:7]
    }