from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from core.permissions import role_required

from .forms import (
    FacultyCreateForm,
    FacultyProfileForm,
    LoginForm,
    StudentProfileForm,
    StudentRegisterForm,
)
from .models import User


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


def register(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    form = StudentRegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="accounts.backends.UsernameOrEmailBackend")
        messages.success(request, f"Welcome aboard, {user.first_name}! Start by creating or joining your project.")
        return redirect("core:dashboard")
    return render(request, "accounts/register.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "You've been signed out.")
    return redirect("core:landing")


@login_required
def settings_view(request):
    user = request.user
    ProfileFormClass = StudentProfileForm if user.is_student else FacultyProfileForm
    profile_form = ProfileFormClass(instance=user)
    password_form = PasswordChangeForm(user)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "profile":
            profile_form = ProfileFormClass(request.POST, request.FILES, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated.")
                return redirect("accounts:settings")
        elif action == "password":
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, password_form.user)
                messages.success(request, "Password changed.")
                return redirect("accounts:settings")
        elif action == "delete":
            if user.check_password(request.POST.get("confirm_password", "")):
                logout(request)
                user.delete()
                messages.info(request, "Your account has been deleted.")
                return redirect("core:landing")
            messages.error(request, "That password is incorrect, so your account was not deleted.")

    return render(
        request,
        "accounts/settings.html",
        {"profile_form": profile_form, "password_form": password_form},
    )


@role_required()  # admins only
def people(request):
    form = FacultyCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        new_user = form.save()
        messages.success(request, f"Created {new_user.get_role_display().lower()} account for {new_user.display_name}.")
        return redirect("accounts:people")

    role = request.GET.get("role", "")
    users = User.objects.order_by("role", "first_name")
    if role:
        users = users.filter(role=role)
    return render(
        request,
        "accounts/people.html",
        {"form": form, "users": users, "role": role, "roles": User.Role.choices},
    )
