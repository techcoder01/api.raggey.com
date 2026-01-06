"""
Custom exception handler for Django REST Framework
Handles authentication errors gracefully and returns consistent responses
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated


def custom_exception_handler(exc, context):
    """
    Custom exception handler that catches authentication errors
    and returns a standardized response for force logout
    """
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)

    # Handle authentication errors (invalid/missing token)
    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        return Response(
            {
                'success': False,
                'error': 'AUTHENTICATION_FAILED',
                'message': 'Your session has expired. Please login again.',
                'force_logout': True,  # Signal to frontend to logout and redirect
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    # For other exceptions, return default response
    return response
