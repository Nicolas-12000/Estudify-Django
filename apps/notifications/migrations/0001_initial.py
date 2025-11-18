# Generated manually to create Notification model
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Fecha y hora de creación del registro', verbose_name='Fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Fecha y hora de última actualización', verbose_name='Fecha de actualización')),
                ('is_active', models.BooleanField(default=True, help_text='Indica si el registro está activo', verbose_name='Activo')),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('message', models.TextField(verbose_name='Message')),
                ('is_read', models.BooleanField(default=False, verbose_name='Is read')),
                ('read_at', models.DateTimeField(blank=True, null=True, verbose_name='Read at')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('notification_type', models.CharField(blank=True, default='generic', max_length=50, verbose_name='Type')),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contenttypes.contenttype')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='users.user', verbose_name='User')),
            ],
            options={
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
            },
        ),
    ]
