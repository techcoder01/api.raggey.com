"""
URL configuration for raggyBackend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def home(request):
    return JsonResponse({
        "status": "OK",
        "service": "Raggey API",
    })

urlpatterns = [
    path('', home),
    path('admin/', admin.site.urls),
    path('admin-dashboard/', include('AdminDashboard.urls', namespace='admin_dashboard')),
    path('dashboard/', include('Dashboard.urls', namespace='dashboard')),
    # Removed: path('auth/', include('Auth.urls', namespace='Auth-api')),  # Empty app
    path('user/', include('User.urls', namespace="User-api")),
    path("fee/", include('Fee.urls',  namespace='Fee-api')),
    path("design/", include('Design.urls',  namespace='Design-api')),
    path("sizes/", include('Sizes.urls',  namespace='Sizes-api')),
    # Removed: path("basket/", include('Basket.urls',  namespace='Basket-api')),  # Not used in frontend
    path("purchase/", include('Purchase.urls',  namespace='Purchase-api')),
    path("api/", include('Coupon.urls')),
    path("banners/", include('Banner.urls')),
]

# Serve media files in development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# Static files are automatically served by django.contrib.staticfiles when DEBUG=True
