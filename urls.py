from django.urls import path
from . import views

urlpatterns = [
    path("", views.accueil, name="accueil"),

    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:book_id>/", views.cart_add, name="cart_add"),
    path("cart/decrease/<int:book_id>/", views.cart_decrease, name="cart_decrease"),
    path("cart/remove/<int:book_id>/", views.cart_remove, name="cart_remove"),

    path("checkout/", views.checkout, name="checkout"),
    path("order/success/<int:order_id>/", views.order_success, name="order_success"),

    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("activate/<uidb64>/<token>/", views.activate_account, name="activate"),
]



