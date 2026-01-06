"""
Force Logout Middleware
Automatically adds force_logout flag to all 401 responses
This ensures Flutter app redirects to login on any authentication failure
"""
import json


class ForceLogoutMiddleware:
    """
    Middleware that intercepts 401 responses and adds force_logout flag
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Check if response is 401 Unauthorized
        if response.status_code == 401:
            # Check if response has JSON content
            content_type = response.get('Content-Type', '')

            if 'application/json' in content_type:
                try:
                    # Parse existing JSON response
                    if hasattr(response, 'data'):
                        # DRF Response object
                        response_data = response.data
                    else:
                        # Regular Django HttpResponse
                        response_data = json.loads(response.content.decode('utf-8'))

                    # Add force_logout flag if not already present
                    if isinstance(response_data, dict):
                        response_data['force_logout'] = True
                        response_data['message'] = response_data.get('message', 'Your session has expired. Please login again.')

                        # Update response content
                        if hasattr(response, 'data'):
                            response.data = response_data
                        else:
                            response.content = json.dumps(response_data).encode('utf-8')

                except (json.JSONDecodeError, AttributeError):
                    # If parsing fails, create new JSON response with force_logout
                    response.content = json.dumps({
                        'success': False,
                        'error': 'AUTHENTICATION_FAILED',
                        'message': 'Your session has expired. Please login again.',
                        'force_logout': True
                    }).encode('utf-8')
                    response['Content-Type'] = 'application/json'

        return response
