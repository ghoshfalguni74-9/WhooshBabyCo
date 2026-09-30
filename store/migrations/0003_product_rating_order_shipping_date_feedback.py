from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import datetime
from store.models import random_product_rating


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0002_product_order_models"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="rating",
            field=models.PositiveSmallIntegerField(default=random_product_rating),
        ),
        migrations.AddField(
            model_name="order",
            name="shipping_date",
            field=models.DateField(default=datetime.date.today),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name="Feedback",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rating", models.PositiveSmallIntegerField()),
                ("review", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="feedback", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
