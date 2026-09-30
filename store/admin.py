from django.contrib.auth import get_user_model
User=get_user_model()

from django.contrib import admin

from .models import Category, Feedback, Order, OrderLine, Product, UserProfile


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "discount_percent", "is_featured")
    list_filter = ("category", "is_featured")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user","email" ,"phone", "city")
    def email(self,obj):
        return obj.user.email
    email.short_description="email"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_id", "user", "status", "payment_method", "total", "created_at")
    list_filter = ("status", "payment_method")
    search_fields = ("order_id", "user__email")


@admin.register(OrderLine)
class OrderLineAdmin(admin.ModelAdmin):
    list_display = ("order", "product_code", "product_name", "quantity", "line_total")
    search_fields = ("product_code", "product_name", "order__order_id")


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("user", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("user__username", "review")
