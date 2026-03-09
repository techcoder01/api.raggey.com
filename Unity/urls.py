from django.urls import path
from . import views

app_name = 'unity'

urlpatterns = [
    path('', views.unity_index, name='unity_index'),
    path('build/<str:filename>', views.serve_unity_build, name='serve_unity_build'),
    path('templatedata/<str:filename>', views.serve_unity_template_data, name='serve_unity_template_data'),
]
