from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username or email")


class StudentRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=40)
    last_name = forms.CharField(max_length=40)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "branch", "division", "roll_no"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ["branch", "division", "roll_no", "email"]:
            self.fields[name].required = True
        domain = settings.ALLOWED_EMAIL_DOMAIN
        if domain:
            self.fields["email"].widget.attrs["placeholder"] = f"you@{domain}"

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        domain = settings.ALLOWED_EMAIL_DOMAIN
        if domain and not email.endswith("@" + domain):
            raise forms.ValidationError(f"Use your college email ending in @{domain}.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.STUDENT
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "bio", "avatar"]
        widgets = {"bio": forms.TextInput(attrs={"placeholder": "One line about you"})}


class StudentProfileForm(ProfileForm):
    class Meta(ProfileForm.Meta):
        fields = ProfileForm.Meta.fields + ["branch", "division", "roll_no"]


class FacultyProfileForm(ProfileForm):
    class Meta(ProfileForm.Meta):
        fields = ProfileForm.Meta.fields + ["designation"]


class FacultyCreateForm(forms.ModelForm):
    """Used by admins to create guide / evaluator accounts."""

    password = forms.CharField(widget=forms.PasswordInput, min_length=8)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "role", "designation"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = [
            (User.Role.GUIDE, "Guide"),
            (User.Role.EVALUATOR, "Evaluator"),
            (User.Role.ADMIN, "Admin"),
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
