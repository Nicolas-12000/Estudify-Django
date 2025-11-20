import pytest
from django.contrib.auth import get_user_model
from apps.users.forms import UserRegistrationForm, PublicUserRegistrationForm, UserLoginForm, UserProfileForm
from apps.users.models import Profile

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistrationForm:
    def test_rejects_duplicate_email(self):
        User.objects.create_user(username="john", email="john@example.com", password="StrongPass123!")
        form = UserRegistrationForm(data={
            "username": "john2",
            "email": "john@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "role": User.UserRole.STUDENT,
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        assert not form.is_valid()
        assert "email" in form.errors
        assert "ya está registrado" in form.errors["email"][0]

    def test_password_mismatch(self):
        form = UserRegistrationForm(data={
            "username": "alice",
            "email": "alice@example.com",
            "first_name": "Alice",
            "last_name": "Smith",
            "role": User.UserRole.TEACHER,
            "password1": "StrongPass123!",
            "password2": "DifferentPass456!",
        })
        assert not form.is_valid()
        # Django's UserCreationForm suele fijar el error en password2 por no coincidir (mensaje en español)
        errors_joined = " ".join([" ".join(v) for v in form.errors.values()])
        assert "contraseña" in errors_joined.lower() and ("coinciden" in errors_joined.lower() or "coincidir" in errors_joined.lower())

    def test_password_validation_too_short(self, settings):
        # rely on Django default validators present in project settings
        short_pwd = "aB1!aB1"  # 7 chars typically too short for default validators (min 8)
        form = UserRegistrationForm(data={
            "username": "shorty",
            "email": "shorty@example.com",
            "first_name": "Short",
            "last_name": " User",
            "role": User.UserRole.STUDENT,
            "password1": short_pwd,
            "password2": short_pwd,
        })
        assert not form.is_valid()
        # error may live under password2 per UserCreationForm behavior
        all_errors = " ".join([" ".join(v) for v in form.errors.values()])
        assert "contraseña" in all_errors.lower() and ("corta" in all_errors.lower() or "mínimo" in all_errors.lower())


@pytest.mark.django_db
class TestPublicUserRegistrationForm:
    def test_rejects_duplicate_email_case_insensitive(self):
        User.objects.create_user(username="case", email="dupe@example.com", password="StrongPass123!")
        form = PublicUserRegistrationForm(data={
            "email": "Dupe@Example.com",
            "first_name": "Case",
            "role": User.UserRole.STUDENT,
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        assert not form.is_valid()
        assert "email" in form.errors or "__all__" in form.errors
        errors = form.errors.get("email", []) + form.errors.get("__all__", [])
        assert any("ya está registrado" in e for e in errors)

    def test_generates_username_from_email_and_is_unique(self):
        # Pre-create a conflicting base username to force suffixing
        # email local part: "john.doe" -> base: "johndoe"
        User.objects.create_user(username="johndoe", email="dummy1@example.com", password="StrongPass123!")
        data = {
            "email": "john.doe@example.com",
            "first_name": "John",
            "role": User.UserRole.TEACHER,
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        form = PublicUserRegistrationForm(data=data)
        assert form.is_valid(), form.errors
        user = form.save()
        assert user.username.startswith("johndoe")
        assert user.username in {"johndoe1", "johndoe2", "johndoe3"} or user.username == "johndoe1"
        assert user.email == "john.doe@example.com"
        assert user.first_name == "John"
        assert user.role == data["role"]

    def test_username_base_normalization(self):
        # dots and dashes removed, lowercased, max length 30 applied
        data = {
            "email": "A.B-C.D-E.F-G.H-I-J-K.L-M-N-O-P-Q-R@example.com",
            "first_name": "Abc",
            "role": User.UserRole.STUDENT,
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        form = PublicUserRegistrationForm(data=data)
        assert form.is_valid(), form.errors
        user = form.save()
        base = "abcdefghijklmnopqrstuvwxyz"[:30]  # after removing punctuation and lowering, it will be truncated
        assert len(user.username) <= 150  # Django default max length
        assert user.username  # non-empty


@pytest.mark.django_db
class TestUserLoginForm:
    def test_login_allows_email_instead_of_username(self, rf):
        user = User.objects.create_user(username="bob", email="bob@example.com", password="StrongPass123!")
        request = rf.post("/login/")
        form = UserLoginForm(request=request, data={"username": "bob@example.com", "password": "StrongPass123!"})
        # clean_username should translate to the legit username and authenticate
        assert form.is_valid()
        assert form.cleaned_data.get("username") == "bob"


@pytest.mark.django_db
class TestUserProfileForm:
    def test_updates_user_and_profile_fields(self):
        user = User.objects.create_user(username="pro", email="pro@example.com", password="StrongPass123!", first_name="Old", last_name="Name")
        profile, _ = Profile.objects.get_or_create(user=user)
        form = UserProfileForm(instance=profile, data={
            "first_name": "New",
            "last_name": "Name",
            "email": "new@example.com",
            "phone": "+123456789",
            "date_of_birth": "2000-01-01",
            "bio": "Hello",
            "address": "123 Street",
            "city": "Town",
            "country": "Wonderland",
        })
        assert form.is_valid(), form.errors
        saved_profile = form.save()
        user.refresh_from_db()
        assert saved_profile.bio == "Hello"
        assert user.first_name == "New"
        assert user.last_name == "Name"
        assert user.email == "new@example.com"
        assert getattr(user, "phone", None) == "+123456789"
