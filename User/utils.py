from django.shortcuts import get_object_or_404
from .models import Profile
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.mail import send_mail


def clean_username(self, username):
    if User.objects.filter(username=username).exists():
        return False
    else:
        return True


def clean_email_check(self, email):
    if User.objects.filter(email=email).exists():
        return False
    else:
        return True


def clean_profile_check(self, user):
    if Profile.objects.filter(user=user).exists():
        return False
    else:
        return True
