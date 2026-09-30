import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.conf import settings
from django.utils import timezone

from .forms import UserProfileForm, UserSignupForm
from .models import Category, Feedback, Order, OrderLine, Product, UserProfile


def ensure_seed_data():
    categories = [
        ("soap", "Soap", "Gentle cleansing bars for delicate baby skin."),
        ("shampoo", "Shampoo", "Tear-free hair care for little ones."),
        ("oil", "Oil", "Daily massage oils and nourishing care."),
        ("clothes", "Clothes", "Comfort-first essentials for everyday wear."),
        ("toys", "Toys", "Safe and playful learning tools for babies."),
        ("accessories", "Accessories", "Useful everyday extras for home and travel."),
    ]

    default_products = {
        "soap": [
            ("johnsons-baby-soap", "Johnson's Baby Soap", "Mild cleansing bar for delicate skin.", 65, "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQXcF4va0ISooFZe8i_2qQpygI-EWxI3iyEYc_zgIt2Kw&s=10", True),
            ("himalaya-nourishing-baby-soap", "Himalaya Nourishing Baby Soap", "Cleanses and nourishes delicate skin.", 84, "https://www.clickoncare.com/cdn/shop/files/4_3b591577-9065-4590-b330-735fabd69be9.jpg?v=1716378231", True),
            ("cetaphil-baby-soap", "Cetaphil Baby Soap", "Mild and gentle soap for sensitive skin.", 99, "https://m.media-amazon.com/images/I/51bFpsWdUPL.jpg", False),
        ],
        "shampoo": [
            ("johnsons-baby-shampoo", "Johnson's Baby Shampoo", "A gentle wash with aloe vera and vitamin B5.", 125, "https://images.ctfassets.net/j62l7jj24jl8/39tZXffnAfykKscf9zj3o2/c4cdf5192e9bfc0a239d248d63bc8024/nmt_image_1_new-hi-in", True),
            ("himalaya-baby-shampoo", "Himalaya Baby Shampoo", "Hibiscus & Chickpeas for growing hair.", 119, "https://assets.myntassets.com/h_1440,q_75,w_1080/v1/assets/images/10887208/2020/7/22/ff7eb98b-3d1e-4de9-b75d-c88050bc39071595425866678HimalayaBabyGentleBabyShampoo100Ml1.jpg", True),
            ("cetaphil-baby-shampoo", "Cetaphil Baby Shampoo", "Natural Chamomile for a comfortable scalp.", 279, "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQVbwQsqRiZUMQWGK8yjxrHK-zY71iyen-CrUSEVZE7QykdjgA53sY6uQJw&s=10", False),
        ],
        "oil": [
            ("johnsons-baby-oil", "Johnson's Baby Oil", "A lightweight oil for after-bath massage.", 149, "https://m.media-amazon.com/images/I/61-7GiP9nvL.jpg", True),
            ("vircoco-coconut-oil", "Vircoco Coconut Oil", "A virgin nourishing oil & cold pressed.", 309, "https://m.media-amazon.com/images/I/41uI59GFFkL.jpg", True),
            ("himalaya-baby-oil", "Himalaya Baby Oil", "A calming addition to a bedtime routine.", 269, "https://cdn.salla.sa/DGdDlG/16228cd8-1051-43ec-b9c6-6f4dd8f92ec7-1000x1000-kJu0YcTEDtdqCpUWo4UXsUrXMfxaHBEvDSJgH57q.jpg", False),
        ],
        "clothes": [
            ("organic-cotton-romper", "Organic Cotton Romper", "Breathable cotton with easy-change fastening.", 499, "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=500&q=80", True),
            ("soft-knitted-bodysuit", "Soft Knitted Bodysuit", "Warm, easy to wear comfort for all-day play.", 420, "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=500&q=80", False),
        ],
        "toys": [
            ("wooden-stacking-set", "Wooden Stacking Set", "Simple shapes encouraging sorting and balance.", 449, "https://storeassets.im-cdn.com/media-manager/channapatnatoysin/oMkclONxQACrWv12tGxu_channapatna-montessori-toys-set-meeran-03_0x0_webp.jpg", True),
            ("soft-rattle-balls", "Soft Rattle Balls", "A fun sensory toy for tiny hands.", 299, "https://images.unsplash.com/photo-1516627145497-ae6968895b74?auto=format&fit=crop&w=500&q=80", False),
        ],
        "accessories": [
            ("baby-bottle-warmer", "Baby Bottle Warmer", "Keeps feeds warm and ready to use.", 699, "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=500&q=80", True),
            ("travel-diaper-bag", "Travel Diaper Bag", "A practical carry-all for daily outings.", 899, "https://images.unsplash.com/photo-1528740561666-dc2479dc08ab?auto=format&fit=crop&w=500&q=80", False),
        ],
    }

    for slug, name, description in categories:
        category, _ = Category.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "description": description},
        )
        for product_slug, product_name, product_description, product_price, product_image, is_featured in default_products.get(slug, []):
            Product.objects.get_or_create(
                slug=product_slug,
                defaults={
                    "category": category,
                    "name": product_name,
                    "description": product_description,
                    "price": product_price,
                    "discount_percent": 15,
                    "image": product_image,
                    "is_featured": is_featured,
                },
            )


def home(request):
    ensure_seed_data()
    featured = Product.objects.filter(is_featured=True)[:3]
    return render(request, "store/home.html", {"featured": featured})


def contact(request):
    submitted = False
    if request.method == "POST":
        submitted = all(request.POST.get(field, "").strip() for field in ("name", "email", "message"))
    return render(request, "store/contact.html", {"submitted": submitted, "feedback": Feedback.objects.select_related("user")})


def appointment(request):
    result = None
    if request.method == "POST":
        child_name = request.POST.get("child_name", "").strip()
        parent_name = request.POST.get("parent_name", "").strip()
        city = request.POST.get("city", "").strip()
        checkup_type = request.POST.get("checkup_type", "").strip()
        if child_name and parent_name and city and checkup_type:
            result = {
                "child_name": child_name,
                "parent_name": parent_name,
                "city": city,
                "checkup_type": checkup_type,
            }
    return render(request, "store/appointment.html", {"result": result})


def nutrition(request):
    result = None
    if request.method == "POST":
        try:
            age = float(request.POST.get("age", ""))
            height = float(request.POST.get("height", ""))
            weight = float(request.POST.get("weight", ""))
            activity = request.POST.get("activity", "normal")
            preference = request.POST.get("preference", "mixed")
            if age < 1 or age > 18 or height <= 0 or weight <= 0:
                raise ValueError

            activity_factor = {"low": 1.0, "normal": 1.15, "active": 1.3}[activity]
            calories = round((1000 + (age * 100)) * activity_factor)
            protein = round(weight * (1.0 if age < 4 else 0.95), 1)
            water = round(weight * 35)
            diet = {
                "veg": "dal, paneer, beans, leafy vegetables, fruit, and whole grains",
                "nonveg": "eggs, chicken, fish, vegetables, fruit, and whole grains",
                "mixed": "eggs or fish, dal, vegetables, fruit, and whole grains",
            }[preference]
            result = {
                "age": age,
                "height": height,
                "weight": weight,
                "calories": calories,
                "protein": protein,
                "water": water,
                "diet": diet,
            }
        except (KeyError, TypeError, ValueError):
            result = {"error": "Please enter valid age, height, weight, activity, and food preference values."}
    return render(request, "store/nutrition.html", {"result": result})


def growth(request):
    return render(request, "store/growth.html")


def cart(request):
    return render(request, "store/cart.html")


def checkout(request):
    profile = getattr(request.user, "profile", None) if request.user.is_authenticated else None
    return render(request, "store/checkout.html", {
        "customer_name": request.user.get_full_name() if request.user.is_authenticated else "",
        "customer_phone": profile.phone if profile else "",
        "customer_address": profile.address if profile else "",
    })


def payment(request):
    return render(request, "store/payment.html", {
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
    })


def razorpay_order(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required."}, status=405)
    try:
        payload = json.loads(request.body)
        amount = Decimal(str(payload.get("amount", "0")))
        if amount <= 0 or amount > Decimal("1000000"):
            raise InvalidOperation
    except (InvalidOperation, TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Enter a valid order amount."}, status=400)

    customer = payload.get("customer") or {}
    cart = payload.get("cart") or []
    order = create_order_from_cart(request, cart, customer, "online")
    if not order:
        return JsonResponse({"error": "Your cart contains no valid products."}, status=400)

    key_id = settings.RAZORPAY_KEY_ID
    key_secret = settings.RAZORPAY_KEY_SECRET
    if not key_id or not key_secret:
        return JsonResponse({"error": "Online payments are not configured yet. Choose Cash on delivery."}, status=503)
    try:
        import razorpay
        razorpay_order = razorpay.Client(auth=(key_id, key_secret)).order.create({
            "amount": int(order.total * 100),
            "currency": "INR",
            "receipt": order.order_id,
        })
    except (ImportError, Exception) as error:
        return JsonResponse({"error": f"Unable to start online payment: {error}"}, status=502)
    return JsonResponse({
        "order_id": razorpay_order["id"],
        "amount": int(order.total * 100),
        "key_id": key_id,
        "store_order_id": order.order_id,
        "shipping_date": order.shipping_date.isoformat(),
    })


def verify_payment(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required."}, status=405)
    try:
        payload = json.loads(request.body)
        message = f"{payload['razorpay_order_id']}|{payload['razorpay_payment_id']}".encode()
        expected = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(), message, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, payload["razorpay_signature"]):
            raise ValueError
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Payment verification failed."}, status=400)
    order = Order.objects.filter(order_id=payload.get("store_order_id"), user=request.user).first()
    if order:
        order.status = "paid"
        order.save(update_fields=["status"])
    return JsonResponse({"success": True, "order_id": order.order_id if order else ""})


def create_order_from_cart(request, cart, customer, payment_method):
    if not request.user.is_authenticated:
        return None
    products = {product.product_code: product for product in Product.objects.filter(product_code__in=[item.get("product_code") for item in cart])}
    lines = []
    subtotal = Decimal("0")
    for item in cart:
        product = products.get(item.get("product_code"))
        quantity = max(int(item.get("quantity", 0)), 0)
        if not product or not quantity:
            continue
        line_subtotal = product.price * quantity
        subtotal += line_subtotal
        lines.append((product, quantity, line_subtotal))
    if not lines:
        return None
    first_order = not Order.objects.filter(user=request.user, status__in=("paid", "placed")).exists()
    discount = (subtotal * Decimal("0.15")).quantize(Decimal("0.01")) if first_order else Decimal("0")
    discounted_subtotal = subtotal - discount
    gst = (discounted_subtotal * Decimal("0.18")).quantize(Decimal("0.01"))
    order = Order.objects.create(
        user=request.user,
        customer_name=customer.get("name", "").strip(),
        customer_phone=customer.get("phone", "").strip(),
        customer_address=customer.get("address", "").strip(),
        payment_method=payment_method,
        subtotal=subtotal,
        first_order_discount=discount,
        gst=gst,
        total=discounted_subtotal + gst,
        shipping_date=timezone.localdate() + timedelta(days=7),
        status="placed" if payment_method == "cod" else "pending",
    )
    for product, quantity, line_subtotal in lines:
        line_discount = (line_subtotal * Decimal("0.15")).quantize(Decimal("0.01")) if first_order else Decimal("0")
        OrderLine.objects.create(
            order=order, product=product, product_code=product.product_code,
            product_name=product.name, quantity=quantity, unit_price=product.price,
            discount_amount=line_discount, line_total=line_subtotal - line_discount,
        )
    return order


def place_cod_order(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required."}, status=405)
    payload = json.loads(request.body)
    order = create_order_from_cart(request, payload.get("cart", []), payload.get("customer", {}), "cod")
    if not order:
        return JsonResponse({"error": "Your cart contains no valid products."}, status=400)
    return JsonResponse({
        "success": True,
        "order_id": order.order_id,
        "total": str(order.total),
        "shipping_date": order.shipping_date.isoformat(),
    })


@login_required(login_url="login_page")
def submit_feedback(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required."}, status=405)
    try:
        payload = json.loads(request.body)
        rating = int(payload.get("rating", 0))
    except (TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Please choose a rating."}, status=400)
    review = str(payload.get("review", "")).strip()
    if rating not in range(1, 6):
        return JsonResponse({"error": "Please choose a rating from 1 to 5."}, status=400)
    Feedback.objects.create(user=request.user, rating=rating, review=review)
    return JsonResponse({"success": True})


def category(request, category):
    ensure_seed_data()
    category_obj = Category.objects.filter(slug=category).first()
    products = Product.objects.filter(category=category_obj) if category_obj else []
    return render(request, "store/category.html", {"category": category_obj.name if category_obj else category.title(), "products": products})


@login_required(login_url="login_page")
def profile(request):
    user = request.user
    profile_obj, _ = UserProfile.objects.get_or_create(user=user)
    form = UserProfileForm(
        initial={
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": profile_obj.phone,
            "city": profile_obj.city,
            "district": profile_obj.district,
            "country": profile_obj.country,
            "address": profile_obj.address,
        }
    )
    if request.method == "POST":
        form = UserProfileForm(request.POST)
        if form.is_valid():
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.email = form.cleaned_data["email"]
            user.username = form.cleaned_data["email"]
            user.save()
            profile_obj.phone = form.cleaned_data["phone"]
            profile_obj.city = form.cleaned_data["city"]
            profile_obj.district = form.cleaned_data["district"]
            profile_obj.country = form.cleaned_data["country"]
            profile_obj.address = form.cleaned_data["address"]
            profile_obj.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("profile")
    return render(request, "store/profile.html", {"form": form})


def login_page(request):
    next_url = request.GET.get("next") or request.POST.get("next") or "home"
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect(next_url)
        messages.error(request, "Invalid email or password.")
    return render(request, "store/login.html", {"next_url": next_url})


def logout_page(request):
    logout(request)
    return redirect("home")


def signup(request):
    form = UserSignupForm()
    next_url = request.GET.get("next") or request.POST.get("next") or "home"
    if next_url != "home":
        request.session["signup_next"] = next_url
    if request.method == "POST":
        form = UserSignupForm(request.POST)
        if form.is_valid():
            otp = f"{secrets.randbelow(900000) + 100000}"
            request.session["pending_signup"] = {
                "data": form.cleaned_data,
                "otp": otp,
                "expires_at": time.time() + 300,
            }
            try:
                send_mail(
                    "Whoosh BabyCo email verification",
                    f"Your Whoosh verification code is {otp}. It is valid for 5 minutes.",
                    settings.DEFAULT_FROM_EMAIL,
                    [form.cleaned_data["email"]],
                    fail_silently=False,
                )
            except Exception:
                request.session.pop("pending_signup", None)
                messages.error(request, "We could not send the verification email. Please try again later.")
            else:
                return redirect("verify_signup")
    return render(request, "store/signup.html", {"form": form, "next_url": next_url})


def verify_signup(request):
    pending = request.session.get("pending_signup")
    if not pending:
        messages.error(request, "Your signup session has expired. Please create your account again.")
        return redirect("signup")
    if time.time() > pending["expires_at"]:
        request.session.pop("pending_signup", None)
        messages.error(request, "That verification code expired. Please create your account again.")
        return redirect("signup")
    if request.method == "POST":
        if secrets.compare_digest(request.POST.get("otp", "").strip(), pending["otp"]):
            data = pending["data"]
            user = User.objects.create_user(
                username=data["email"],
                email=data["email"],
                password=data["password1"],
                first_name=data["first_name"],
                last_name=data.get("last_name", ""),
            )
            UserProfile.objects.create(user=user, phone=data.get("phone", ""))
            request.session.pop("pending_signup", None)
            login(request, user)
            return redirect(request.session.pop("signup_next", "home"))
        messages.error(request, "Invalid verification code.")
    return render(request, "store/verify_signup.html", {"email": pending["data"]["email"]})
