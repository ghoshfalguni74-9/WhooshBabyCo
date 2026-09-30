from django.contrib.auth.models import User
from django.db import models
import uuid
import random


def random_product_rating():
    return random.randint(3, 4)


def generate_order_id():
    return f"WB-{uuid.uuid4().hex[:14].upper()}"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    product_code = models.CharField(max_length=24, unique=True, editable=False, default="")
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.PositiveIntegerField(default=5)
    image = models.URLField(max_length=500, blank=True)
    is_featured = models.BooleanField(default=False)
    rating = models.PositiveSmallIntegerField(default=random_product_rating)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.product_code:
            self.product_code = f"WB-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    @property
    def discount(self):
        return self.discount_percent

    @property
    def discounted_price(self):
        if self.discount_percent:
            multiplier = (100 - self.discount_percent) / 100
            return round(float(self.price) * multiplier, 2)
        return self.price


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.email


class Order(models.Model):
    PAYMENT_CHOICES = [("online", "Online Payment"), ("cod", "Cash on delivery")]
    STATUS_CHOICES = [("pending", "Pending"), ("paid", "Paid"), ("placed", "Placed")]
    order_id = models.CharField(max_length=32, unique=True, default=generate_order_id, editable=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
    customer_name = models.CharField(max_length=120)
    customer_phone = models.CharField(max_length=30)
    customer_address = models.TextField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    first_order_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst = models.DecimalField(max_digits=12, decimal_places=2)
    donation_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)


class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_code = models.CharField(max_length=24)
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)


class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="feedback")
    rating = models.PositiveSmallIntegerField()
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
