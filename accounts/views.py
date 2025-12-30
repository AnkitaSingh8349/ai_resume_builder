from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from .forms import SignupForm


# ===============================
# HOME
# ===============================
def home(request):
    return render(request, "home.html")


# ===============================
# LOGIN (EMAIL BASED)
# ===============================
def login_view(request):

    if request.method == "GET":
        return render(request, "accounts/login.html")

    email = request.POST.get("username")   # email comes from frontend
    password = request.POST.get("password")

    if not email or not password:
        return JsonResponse(
            {"success": False, "error": "Email and password are required"}
        )

    try:
        user_obj = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Invalid email or password"}
        )

    # 🔑 Authenticate using username (which we set = email)
    user = authenticate(
        request,
        username=user_obj.username,
        password=password
    )

    if user is None:
        return JsonResponse(
            {"success": False, "error": "Invalid email or password"}
        )

    login(request, user)

    return JsonResponse(
        {"success": True, "redirect": "/dashboard/"}
    )


# ===============================
# REGISTER
# ===============================
def register_view(request):

    if request.method == "GET":
        return render(request, "accounts/register.html", {
            "form": SignupForm()
        })

    form = SignupForm(request.POST)

    if form.is_valid():
        email = form.cleaned_data["email"]

        if User.objects.filter(email=email).exists():
            return JsonResponse(
                {"success": False, "error": "Email already exists"}
            )

        user = form.save(commit=False)

        # 🔥 MOST IMPORTANT FIX
        user.username = email          # username MUST exist
        user.set_password(form.cleaned_data["password1"])
        user.save()

        login(request, user)

        return JsonResponse(
            {"success": True, "redirect": "/dashboard/"}
        )

    error = list(form.errors.values())[0][0]
    return JsonResponse(
        {"success": False, "error": error}
    )


# ===============================
# DASHBOARD
# ===============================
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("login")
    return render(request, "dashboard.html")


# ===============================
# LOGOUT
# ===============================
def logout_view(request):
    logout(request)
    return redirect("login")
