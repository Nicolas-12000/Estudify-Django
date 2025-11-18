"""Backfill helper: migrate legacy `Course.schedule` text to normalized schedule models.

Lifecycle and usage:
- Use `--dry-run` on staging to export parsing failures to review (`--failures-file`).
- When dry-run is clean, run the real backfill during a maintenance window.
- Keep this command in the repository for a short rotation (1-2 deploy cycles)
    after the real backfill is executed and the migration that drops the legacy
    fields has been applied. The command intentionally uses `getattr(course, 'schedule', '')`
    so it can still read legacy values even if the `schedule` attribute is no
    longer present on the `Course` model in this codebase. Delete the command
    only after all deploy targets have been confirmed migrated and the backfill
    is no longer needed.

This file should not be removed until you are certain all environments have
run the real backfill + schema migration.
"""

from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from apps.courses.models import Course, TimeSlot, Classroom, CourseSession
import re

DAY_MAP = {
    'lun': 0, 'lunes': 0,
    'mar': 1, 'martes': 1,
    'mie': 2, 'mié': 2, 'miercoles': 2, 'miércoles': 2,
    'jue': 3, 'jueves': 3,
    'vie': 4, 'viernes': 4,
    'sab': 5, 'sabado': 5, 'sábado': 5,
    'dom': 6, 'domingo': 6,
}

# Accept times like '8', '08', '8:00', '08:00' and day/time separators like ',' or ';'
TIME_RE = re.compile(
    r"(?P<day>[A-Za-zÁÉÍÓÚáéíóúñÑ]+)\s+(?P<start>\d{1,2}(?::\d{2})?)-(?P<end>\d{1,2}(?::\d{2})?)"
)


class Command(BaseCommand):
    help = 'Migra Course.schedule textual a TimeSlot + CourseSession'

    def handle(self, *args, **options):
        """Entry point: recorre cursos y procesa su `schedule` si existe.

        Se delega la lógica a helpers para mantener la complejidad baja y
        facilitar pruebas unitarias.
        """
        total_courses = Course.objects.count()
        self.stdout.write(f"Procesando {total_courses} cursos...")

        # get dry-run flag from parsed options
        dry_run = options.get('dry_run', False)

        created = {
            'timeslots': 0,
            'classrooms': 0,
            'sessions': 0,
        }
        failures = []

        if dry_run:
            self.stdout.write('Modo dry-run: no se harán escrituras en la base de datos')

        for course in Course.objects.all():
            schedule = (getattr(course, 'schedule', '') or '').strip()
            if not schedule:
                continue
            # accept either ';' or ',' as separators in the legacy field
            normalized = schedule.replace(',', ';')
            parts = [p.strip() for p in normalized.split(';') if p.strip()]
            for entry in parts:
                # delegate entry processing to helper to reduce complexity here
                self._process_entry(course, entry, created, failures, dry_run=dry_run)
        # If requested, dump failures to JSON for easier review in staging
        failures_file = options.get('failures_file')
        if failures_file and failures:
            try:
                import json

                with open(failures_file, 'w', encoding='utf-8') as fh:
                    json.dump([
                        {'course_id': f[0], 'course_name': f[1], 'entry': f[2], 'error': f[3] if len(f) > 3 else None}
                        for f in failures
                    ], fh, ensure_ascii=False, indent=2)
                self.stdout.write(f"Fallos escritos en {failures_file}")
            except Exception as exc:
                self.stderr.write(f"No se pudo escribir archivo de fallos: {exc}")

        self.stdout.write(f"Timeslots creados: {created['timeslots']}")
        self.stdout.write(f"Classrooms creados: {created['classrooms']}")
        self.stdout.write(f"Sessions creadas: {created['sessions']}")
        if failures:
            self.stdout.write("Fallos encontrados (curso_id, curso_name, entrada[, error]):")
            for f in failures:
                self.stdout.write(str(f))
        else:
            self.stdout.write("Migración completada sin fallos.")

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='Previsualiza los cambios sin escribir en la base de datos',
        )
        parser.add_argument(
            '--failures-file',
            dest='failures_file',
            help='Ruta a un archivo JSON donde volcar las entradas que no pudieron parsearse/validarse',
            required=False,
        )

    def _parse_entry(self, text):
        """Parsea una entrada tipo 'Lun 08:00-10:00' y devuelve (day,start,end) o None."""
        m = TIME_RE.match(text)
        if not m:
            return None
        day_raw = m.group('day').lower()
        day_key = day_raw[:3]
        day = DAY_MAP.get(day_key) if DAY_MAP.get(day_key) is not None else DAY_MAP.get(day_raw)
        if day is None:
            return None
        start = m.group('start')
        end = m.group('end')

        # normalize times: if given as '8' or '8:00' -> convert to '08:00'
        def norm(t):
            if ':' not in t:
                # only hour provided
                hour = int(t)
                return "{:02d}:00".format(hour)
            h, mm = t.split(':')
            return "{:02d}:{:02d}".format(int(h), int(mm))

        try:
            start_n = norm(start)
            end_n = norm(end)
        except ValueError:
            return None
        return day, start_n, end_n

    def _process_entry(self, course, entry, created, failures, dry_run=False):
        """Procesa una entrada individual de schedule para un curso.

        Encapsula la creación de TimeSlot, Classroom y CourseSession.
        """
        parsed = self._parse_entry(entry)
        if not parsed:
            failures.append((course.id, course.name, entry))
            return

        day, start, end = parsed

        # find or create timeslot (or simulate in dry-run)
        ts = self._get_or_create_timeslot(day, start, end, dry_run, created)

        # find or create classroom (or simulate)
        classroom_obj = self._get_or_create_classroom(getattr(course, 'classroom', None), dry_run, created)

        # validate or save session
        try:
            self._validate_or_save_session(course, ts, classroom_obj, day, start, end, dry_run, created, failures, entry)
        except ValidationError as exc:
            failures.append((course.id, course.name, entry, str(exc)))

    def _get_or_create_timeslot(self, day, start, end, dry_run, created):
        """Return a TimeSlot instance. In dry-run may return an unsaved instance for validation."""
        ts = TimeSlot.objects.filter(day_of_week=day, start_time=start, end_time=end).first()
        if ts:
            return ts

        if dry_run:
            # Return an unsaved TimeSlot for validation purposes
            created['timeslots'] += 1
            return TimeSlot(day_of_week=day, start_time=start, end_time=end)

        # real create
        ts, _ = TimeSlot.objects.get_or_create(day_of_week=day, start_time=start, end_time=end)
        created['timeslots'] += 1
        return ts

    def _get_or_create_classroom(self, classroom_name, dry_run, created):
        """Return a Classroom instance or None. In dry-run may return None or unsaved instance."""
        if not classroom_name:
            return None

        cls = Classroom.objects.filter(name=classroom_name).first()
        if cls:
            return cls

        if dry_run:
            created['classrooms'] += 1
            return Classroom(name=classroom_name)

        cls, _ = Classroom.objects.get_or_create(name=classroom_name)
        created['classrooms'] += 1
        return cls

    def _validate_or_save_session(self, course, ts, classroom_obj, day, start, end, dry_run, created, failures, entry):
        """Validate (dry-run) or save a CourseSession. Append failures on ValidationError."""
        if dry_run:
            # ts may be unsaved; use it for validation
            sess = CourseSession(course=course, timeslot=ts, classroom_fk=classroom_obj)
            sess.full_clean()
            created['sessions'] += 1
            return

        # real write path; ts should be a saved instance
        sess = CourseSession(course=course, timeslot=ts, classroom_fk=classroom_obj)
        sess.full_clean()
        sess.save()
        created['sessions'] += 1
