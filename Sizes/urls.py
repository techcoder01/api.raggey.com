from django.urls import path, include
from .views import FetchSizesAPIView, SizesDetailAPIView
from .measurement_views import (
    DefaultMeasurementListAPIView,
    DefaultMeasurementDetailAPIView,
    CustomMeasurementListAPIView,
    CustomMeasurementDetailAPIView,
    AllMeasurementsListAPIView,
    AdminAllCustomMeasurementsAPIView,
    AdminUserCustomMeasurementsAPIView,
    AdminCustomMeasurementDetailAPIView
)

urlpatterns = [
    # ============ OLD SIZES ENDPOINTS (BACKWARD COMPATIBILITY) =======================================
    path('fetch/sizes/', FetchSizesAPIView.as_view()),
    path('detail/size/<int:pk>/', SizesDetailAPIView.as_view()),
    path('create/size/', SizesDetailAPIView.as_view()),
    path('update/size/<int:pk>/', SizesDetailAPIView.as_view()),
    path('delete/size/<int:pk>/', SizesDetailAPIView.as_view()),

    # ============ DEFAULT MEASUREMENTS (Admin) =======================================
    path('measurements/default/', DefaultMeasurementListAPIView.as_view()),
    path('measurements/default/<int:pk>/', DefaultMeasurementDetailAPIView.as_view()),
    path('measurements/default/create/', DefaultMeasurementDetailAPIView.as_view()),
    path('measurements/default/update/<int:pk>/', DefaultMeasurementDetailAPIView.as_view()),
    path('measurements/default/delete/<int:pk>/', DefaultMeasurementDetailAPIView.as_view()),

    # ============ CUSTOM MEASUREMENTS (User-specific) =======================================
    path('measurements/custom/', CustomMeasurementListAPIView.as_view()),
    path('measurements/custom/<int:pk>/', CustomMeasurementDetailAPIView.as_view()),
    path('measurements/custom/create/', CustomMeasurementListAPIView.as_view()),
    path('measurements/custom/update/<int:pk>/', CustomMeasurementDetailAPIView.as_view()),
    path('measurements/custom/delete/<int:pk>/', CustomMeasurementDetailAPIView.as_view()),

    # ============ COMBINED MEASUREMENTS (All available measurements for user) =======================================
    path('measurements/all/', AllMeasurementsListAPIView.as_view()),

    # ============ ADMIN ENDPOINTS (View All Users' Measurements) =======================================
    path('admin/measurements/custom/all/', AdminAllCustomMeasurementsAPIView.as_view()),
    path('admin/measurements/custom/user/<int:user_id>/', AdminUserCustomMeasurementsAPIView.as_view()),
    path('admin/measurements/custom/<int:pk>/', AdminCustomMeasurementDetailAPIView.as_view()),
    path('admin/measurements/custom/update/<int:pk>/', AdminCustomMeasurementDetailAPIView.as_view()),
    path('admin/measurements/custom/delete/<int:pk>/', AdminCustomMeasurementDetailAPIView.as_view()),
]

app_name = 'Sizes-api'
