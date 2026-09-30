from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("home/", views.home, name="home_alias"),
    path("contact/", views.contact, name="contact"),
    path("nutrition/", views.nutrition, name="nutrition"),
    path("growth/", views.growth, name="growth"),
    path("appointment/", views.appointment, name="appointment"),
    path("cart/", views.cart, name="cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("payment/", views.payment, name="payment"),
    path("api/razorpay/order/", views.razorpay_order, name="razorpay_order"),
    path("api/razorpay/verify/", views.verify_payment, name="verify_payment"),
    path("api/orders/cod/", views.place_cod_order, name="place_cod_order"),
    path("api/feedback/", views.submit_feedback, name="submit_feedback"),
    path("profile/", views.profile, name="profile"),
    path("login/", views.login_page, name="login_page"),
    path("signup/", views.signup, name="signup"),
    path("signup/verify/", views.verify_signup, name="verify_signup"),
    path("logout/", views.logout_page, name="logout"),
    path("category/<str:category>/", views.category, name="category"),
]
