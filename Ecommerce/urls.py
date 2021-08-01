from django.urls import path
from .views import (
HomeView,
ItemDetailView,
add_to_cart,
remove_from_cart,
OrderSummaryView,
remove_single_item_from_cart,
CheckoutView,
PaymentView,
AddCoupon,
RequestRefundView
)
app_name='Ecommerce'
urlpatterns=[
    path('',HomeView.as_view(),name='home'),
    path('Products/<slug>/',ItemDetailView.as_view(),name='Products'),
    path('add-to-cart/<slug>/',add_to_cart,name='add-to-cart'),
    path('remove_from_cart/<slug>/',remove_from_cart,name='remove_from_cart'),
    path('remove_single_item_from_cart/<slug>/',remove_single_item_from_cart,name='remove_single_item_from_cart'),
    path('order-summary/',OrderSummaryView.as_view(),name='order-summary'),
    path('checkout/',CheckoutView.as_view(),name='checkout'),
    path('payment/<payment_option>',PaymentView.as_view(),name='payment'),
    path('add_coupon/',AddCoupon.as_view(),name='add_coupon'),
    path('RequestRefund/',RequestRefundView.as_view(),name='RequestRefund'),
    
    
]