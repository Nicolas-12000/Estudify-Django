from django.contrib.auth import get_user_model

def create_default_admin():
    User = get_user_model()
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            email="admin@gmail.com",
            password="admin123"
        )
        print("✔ Default admin created")
    else:
        print("ℹ Admin user already exists")
