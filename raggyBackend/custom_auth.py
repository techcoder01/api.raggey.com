"""
Custom JWT Authentication with Force Logout Check
Extends JWTAuthentication to check if user should be force logged out
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that checks force logout table
    """

    def authenticate(self, request):
        print(f'🔍 CustomJWTAuthentication called for: {request.path}')

        # First, use default JWT authentication
        result = super().authenticate(request)
        print(f'   JWT Auth result: {result is not None}')

        if result is not None:
            user, token = result
            print(f'   ✅ User: {user.username} (ID: {user.id})')

            # Check if user should be force logged out
            try:
                from User.models import ForceLogoutUser
                should_logout = ForceLogoutUser.should_logout(user)
                print(f'   🔒 Force logout check: {should_logout}')

                if should_logout:
                    print(f'   🚨 FORCING LOGOUT for user: {user.username}')
                    # Remove from force logout list (they'll need to login again)
                    ForceLogoutUser.remove_user(user)
                    print(f'   ✅ Removed from force logout table')

                    # Raise authentication error - will trigger force logout on client
                    print(f'   ❌ Raising AuthenticationFailed')
                    raise AuthenticationFailed(
                        {
                            'success': False,
                            'error': 'AUTHENTICATION_FAILED',
                            'message': 'Your session has expired. Please login again.',
                            'force_logout': True
                        }
                    )
            except AuthenticationFailed:
                # Re-raise AuthenticationFailed - this is what we want!
                print(f'   🔄 Re-raising AuthenticationFailed')
                raise
            except ImportError as e:
                # ForceLogoutUser model not available yet (migration pending)
                print(f'   ⚠️  ImportError: {e}')
                pass
            except Exception as e:
                # Any other error - log but don't break authentication
                print(f'   ⚠️  Warning: Force logout check failed: {e}')
                import traceback
                traceback.print_exc()
                pass

        print(f'   ↩️  Returning result')
        return result
