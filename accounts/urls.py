from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    
    path('validate-step1/', views.validate_step1, name='validate_step1'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('set-password/', views.set_password, name='set_password'), # New URL
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset_request_view, name='password_reset_request'),
    path('password-reset/confirm/', views.password_reset_confirm_view, name='password_reset_confirm'),
    


    # Other Page URLs
    path('about/', views.about, name="about"),
    path('auction/', views.auction, name="auction"),
    path('auction-details/<int:pk>/', views.auc_details, name="auction-details"),
    path('auction-details/<int:pk>/place_bid/', views.place_bid, name="place_bid"),
    path('category_details/<int:pk>/', views.category_details, name="category_details"),
    path('category/',views.category, name="category"),
    path('contact/',views.contact, name="contact"),
    path('sellers/',views.seller_list, name="seller_list"),
    path('sellers/details/<int:pk>  ',views.seller_details, name="seller_details"),
    path('how-to-sell/',views.how_to_sell, name="how-to-sell"),
    path('how-to-bid/',views.how_to_bid, name="how-to-bid"),
    path('faqs/',views.faqs, name="faqs"),
    path('error/',views.error, name="error"),
    path('privacy-policy/',views.privacy_policy, name="privacy_policy"), 
    path('support-center/',views.support_center, name="support_center"), 
    path('terms-condition/',views.terms_condition, name="terms_condition"),
    path('dashboard/',views.dash_board, name="dashboard"),
    path('edit-profile/',views.edit_profile_view, name="edit_profile_view"),
    #For Edit profile
    path('edit-profile/edit/', views.edit_profile, name='edit_profile'),
    path('password/change/', views.change_password, name='change_password'),
    path('help_and_support/',views.help_support, name="help_support"),
    
    #seller and bidder show product and seller add the product

    path('user_auction/',views.user_auction,name="user_auction"),
        #For contect Form
    path('submit-contact/', views.contact_view, name='submit_contact_form'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/', views.user_wishlist_products, name='user_wishlist'),

    # path('blogs/', views.blog, name='blog_list'),
    path('blogs/<int:pk>/', views.blog, name='blog'),
    path('add_blog/',views.add_blog,name="add_blog"),

    path('dashboard-admin/', views.dashboardAdmin, name='dashboard-admin'),
    path('admin-manage-product/', views.adminManageProduct, name='admin-manage-product'),
    path('admin-delete-product/<int:product_id>/', views.deleteProduct, name='delete-product'),
    path('admin-product/new/', views.admin_product_form, name='admin-product-new'),
    path('admin-product/<int:pk>/edit/', views.admin_product_edit, name='admin-product-edit'),
    

    path('admin-manage-category/', views.adminManageCategory, name='admin-manage-category'), 
    path('admin-delete-category/<int:category_id>/', views.deleteCategory, name='delete-category'), 
    # category edit modal endpoint
    path('admin-category/<int:pk>/edit/', views.admin_category_edit, name='admin-category-edit'), 
    # admin users
    path('admin-manage-users/', views.adminManageUsers, name='admin-manage-users'),
    path('admin-user/new/', views.admin_user_new, name='admin-user-new'),
    path('admin-user/<int:pk>/edit/', views.admin_user_edit, name='admin-user-edit'),
    path('admin-user/<int:pk>/delete/', views.admin_user_delete, name='admin-user-delete'),
    # admin reviews
    path('admin-manage-review/', views.adminManageReview, name='admin-manage-review'),
    path('admin-delete-review/<int:review_id>/', views.deleteReview, name='delete-review'),
    # search API
    path('api/instant-search/', views.instant_search, name='instant-search'),

    path('admin-manage-blog/', views.adminManageBlog, name='admin-manage-blog'),
    path('admin-delete-blog/<int:blog_id>/', views.deleteBlog, name='delete-blog'),

    # admin CSV download
    path('admin-manage-product/export-csv/', views.export_products_csv_view, name='export_products_csv'),
]

