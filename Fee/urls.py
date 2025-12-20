from django.urls import path, include
from .views import FeeListAPIVIew, FeeABIVIew, FeeListUserAPIVIew, FeeAreaAPIVIew
urlpatterns = [
    path("create/", FeeABIVIew.as_view()),
    path('update/<int:pk>/', FeeABIVIew.as_view()),
    path('delete/<int:pk>/', FeeABIVIew.as_view()),
    path('detail/<int:pk>/', FeeABIVIew.as_view()),
    path("list/", FeeListAPIVIew.as_view()),
    path("area/", FeeListUserAPIVIew.as_view()),
    path("area/all/", FeeAreaAPIVIew.as_view()),

]

app_name = 'Fee-api'
