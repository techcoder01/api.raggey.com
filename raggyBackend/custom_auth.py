"""
Custom JWT Authentication with Force Logout Check
Extends JWTAuthentication to check if user should be force logged out
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from User.force_logout_model import ForceLogoutUser


class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that checks force logout table
    """

    def authenticate(self, request):
        # First, use default JWT authentication
        result = super().authenticate(request)

        if result is not None:
            user, token = result

            # Check if user should be force logged out
            if ForceLogoutUser.should_logout(user):
                # Remove from force logout list (they'll need to login again)
                ForceLogoutUser.remove_user(user)

                # Raise authentication error - will trigger force logout on client
                raise AuthenticationFailed(
                    {
                        'success': False,
                        'error': 'AUTHENTICATION_FAILED',
                        'message': 'Your session has expired. Please login again.',
                        'force_logout': True
                    }
                )

        return result
