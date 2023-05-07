"""
URL configuration for bloodbank project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import include, path
import app.views as views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/blood_requests/', views.get_blood_requests, name="get all blood requests"),
    path('api/add_blood_request/', views.add_blood_request, name="add blood request"),
    path('api/blood_request/<str:id>', views.get_blood_request_details, name="fetch all attributes of an blood_request"),
    path('api/blood_request/<str:id>', views.delete_blood_request, name="delete blood_request"),
]
