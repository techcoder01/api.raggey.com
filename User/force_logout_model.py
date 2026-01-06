"""
Force Logout Model
Tracks users who should be force logged out
When a user is added to this table, all their API requests will return 401
"""
from django.db import models
from django.contrib.auth.models import User


class ForceLogoutUser(models.Model):
    """
    Users in this table will be force logged out on next API request
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='force_logout')
    created_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'force_logout_users'
        verbose_name = 'Force Logout User'
        verbose_name_plural = 'Force Logout Users'

    def __str__(self):
        return f"Force Logout: {self.user.username}"

    @classmethod
    def should_logout(cls, user):
        """Check if user should be force logged out"""
        return cls.objects.filter(user=user).exists()

    @classmethod
    def add_user(cls, user, reason=None):
        """Add user to force logout list"""
        obj, created = cls.objects.get_or_create(user=user, defaults={'reason': reason})
        return obj

    @classmethod
    def remove_user(cls, user):
        """Remove user from force logout list (after they login again)"""
        cls.objects.filter(user=user).delete()
