from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="target_url",
            field=models.CharField(max_length=512, null=True, blank=True, default=None),
        ),
    ]
