from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0006_menucollection_remove_product_category_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="order_notification_email",
            field=models.EmailField(blank=True, max_length=254, verbose_name="Имейл за известия за поръчки"),
        ),
    ]
