from django.db import migrations
import random


def randomize_ratings(apps, schema_editor):
    Product = apps.get_model("store", "Product")
    for product in Product.objects.all().iterator():
        product.rating = random.choice((3, 4))
        product.save(update_fields=("rating",))


class Migration(migrations.Migration):
    dependencies = [("store", "0003_product_rating_order_shipping_date_feedback")]

    operations = [migrations.RunPython(randomize_ratings, migrations.RunPython.noop)]
