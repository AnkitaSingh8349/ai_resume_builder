from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib import messages
from .forms import SignupForm


# ===============================
# HOME PAGE
# ===============================
def home(request):
    return render(request, "home.html")


# ===============================
# LOGIN VIEW (EMAIL + PASSWORD)
# ===============================
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        email = request.POST.get("username")
        password = request.POST.get("password")

        # -------- VALIDATIONS --------
        if not email or not password:
            return render(
                request,
                "accounts/login.html",
                {"error": "Email and password are required"},
            )

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(
                request,
                "accounts/login.html",
                {"error": "Invalid email or password"},
            )

        user = authenticate(
            request,
            username=user_obj.username,
            password=password,
        )

        if user is None:
            return render(
                request,
                "accounts/login.html",
                {"error": "Invalid email or password"},
            )

        login(request, user)
        return redirect("dashboard")

    return render(request, "accounts/login.html")


# ===============================
# REGISTER VIEW (WITH VALIDATIONS)
# ===============================
def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = SignupForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]

            # -------- EMAIL UNIQUE CHECK --------
            if User.objects.filter(email=email).exists():
                form.add_error("email", "Email already exists")
                return render(
                    request,
                    "accounts/register.html",
                    {"form": form},
                )

            # -------- CREATE USER --------
            user = form.save(commit=False)

            # 🔴 IMPORTANT FIX
            user.username = email   # username must be unique
            user.email = email

            user.set_password(form.cleaned_data["password1"])
            user.save()

            # -------- LOGIN --------
            login(request, user)
            return redirect("dashboard")

        else:
            return render(
                request,
                "accounts/register.html",
                {"form": form},
            )

    else:
        form = SignupForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )



# ===============================
# DASHBOARD VIEW
# ===============================
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("login")

    return render(request, "dashboard.html")


# ===============================
# LOGOUT VIEW
# ===============================
def logout_view(request):
    logout(request)
    return redirect("/accounts/login/")
