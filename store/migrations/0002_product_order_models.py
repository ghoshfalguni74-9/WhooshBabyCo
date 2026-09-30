from django.db import migrations, models
import django.db.models.deletion
import uuid


def product_code():
    return f"WB-{uuid.uuid4().hex[:10].upper()}"


def order_id():
    return f"WB-{uuid.uuid4().hex[:14].upper()}"


def fill_product_codes(apps, schema_editor):
    product_model = apps.get_model("store", "Product")
    for product in product_model.objects.filter(product_code__isnull=True) | product_model.objects.filter(product_code=""):
        product.product_code = product_code()
        product.save(update_fields=["product_code"])


class Migration(migrations.Migration):
    dependencies = [("store", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="product",
            name="product_code",
            field=models.CharField(blank=True, editable=False, max_length=24, null=True),
        ),
        migrations.RunPython(
            fill_product_codes,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="product",
            name="product_code",
            field=models.CharField(editable=False, max_length=24, unique=True),
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_id", models.CharField(default=order_id, editable=False, max_length=32, unique=True)),
                ("customer_name", models.CharField(max_length=120)),
                ("customer_phone", models.CharField(max_length=30)),
                ("customer_address", models.TextField()),
                ("payment_method", models.CharField(choices=[("online", "Online Payment"), ("cod", "Cash on delivery")], max_length=20)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("paid", "Paid"), ("placed", "Placed")], default="pending", max_length=20)),
                ("subtotal", models.DecimalField(decimal_places=2, max_digits=12)),
                ("first_order_discount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("gst", models.DecimalField(decimal_places=2, max_digits=12)),
                ("total", models.DecimalField(decimal_places=2, max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=models.deletion.PROTECT, related_name="orders", to="auth.user")),
            ],
        ),
        migrations.CreateModel(
            name="OrderLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_code", models.CharField(max_length=24)),
                ("product_name", models.CharField(max_length=200)),
                ("quantity", models.PositiveIntegerField()),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=12)),
                ("discount_amount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("line_total", models.DecimalField(decimal_places=2, max_digits=12)),
                ("order", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="lines", to="store.order")),
                ("product", models.ForeignKey(on_delete=models.deletion.PROTECT, to="store.product")),
            ],
        ),
    ]