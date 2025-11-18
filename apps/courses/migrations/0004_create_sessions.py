# Generated migration for adding TimeSlot, Classroom, CourseSession
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_add_classroom_schedule'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimeSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Fecha y hora de creación del registro', verbose_name='Fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Fecha y hora de última actualización', verbose_name='Fecha de actualización')),
                ('is_active', models.BooleanField(default=True, help_text='Indica si el registro está activo', verbose_name='Activo')),
                ('day_of_week', models.IntegerField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
            ],
            options={
                'verbose_name': 'Franja horaria',
                'verbose_name_plural': 'Franjas horarias',
            },
        ),
        migrations.CreateModel(
            name='Classroom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Fecha y hora de creación del registro', verbose_name='Fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Fecha y hora de última actualización', verbose_name='Fecha de actualización')),
                ('is_active', models.BooleanField(default=True, help_text='Indica si el registro está activo', verbose_name='Activo')),
                ('name', models.CharField(max_length=100, verbose_name='Nombre')),
                ('location', models.CharField(max_length=255, blank=True, verbose_name='Ubicación')),
                ('capacity', models.PositiveIntegerField(blank=True, null=True, verbose_name='Capacidad')),
            ],
            options={
                'verbose_name': 'Aula',
                'verbose_name_plural': 'Aulas',
            },
        ),
        migrations.CreateModel(
            name='CourseSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Fecha y hora de creación del registro', verbose_name='Fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Fecha y hora de última actualización', verbose_name='Fecha de actualización')),
                ('is_active', models.BooleanField(default=True, help_text='Indica si el registro está activo', verbose_name='Activo')),
                ('recurrence', models.CharField(blank=True, max_length=50, verbose_name='Recurrencia', help_text='p.ej. weekly')),
                ('notes', models.TextField(blank=True, verbose_name='Notas')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='courses.course')),
                ('timeslot', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sessions', to='courses.timeslot')),
                ('classroom_fk', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sessions', to='courses.classroom')),
            ],
            options={
                'verbose_name': 'Sesión de curso',
                'verbose_name_plural': 'Sesiones de curso',
            },
        ),
        migrations.AddIndex(
            model_name='coursesession',
            index=models.Index(fields=['course', 'timeslot'], name='coursesess_course_timeslot_idx'),
        ),
    ]
