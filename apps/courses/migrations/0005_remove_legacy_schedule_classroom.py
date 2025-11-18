from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0004_create_sessions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='course',
            name='schedule',
        ),
        migrations.RemoveField(
            model_name='course',
            name='classroom',
        ),
    ]
