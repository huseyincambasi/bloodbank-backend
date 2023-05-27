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
    path(
        'api/index/',
        views.index,
        name="return user info if logged in, else return null"
    ),
    path(
        'api/register',
        views.register,
        name="registers user"
    ),
    path(
        'api/login',
        views.login,
        name="logs in user"
    ),
    path(
        'api/reset_password',
        views.reset_password,
        name="resets passwords and sends it via email"
    ),
    path(
        'api/update_password',
        views.update_password,
        name="updates password"
    ),
    path(
        'api/logout',
        views.logout,
        name="logs out user"
    ),
    path(
        'api/logout',
        views.logout,
        name="logs out user"
    ),
    path(
        'api/user/info/',
        views.user_info,
        name="fetch all attributes of user info"
    ),
    path(
        'api/user/donation_date',
        views.user_update_donation_date,
        name="user updates most recent donation date"
    ),
    path(
        'api/user/city',
        views.user_update_city,
        name="user updates city"
    ),
    path(
        'api/user/district',
        views.user_update_district,
        name="user updates district"
    ),
    path(
        'api/user/phone',
        views.user_update_phone,
        name="user updates phone"
    ),
    path(
        'api/user/city_district_phone',
        views.user_update_city_district_phone,
        name="user updates city district and phone"
    ),
    path(
        'api/user/subscribe',
        views.user_subscribe_or_unsubscribe,
        name="user subscribes or unsubscribes to the email list"
    ),
    path(
        'api/user/add_blood_request/',
        views.user_add_blood_request,
        name="add blood request"
    ),
    path(
        'api/user/blood_requests/',
        views.user_blood_requests,
        name="get all blood requests belong to the user"
    ),
    path(
        'api/user/blood_requests/<str:blood_request_id>/',
        views.user_blood_request_details,
        name="fetch all attributes of an blood_request"
    ),
    path(
        'api/user/blood_requests/<str:blood_request_id>/update',
        views.user_blood_request_details_update,
        name="update any attribute of a blood request"
    ),
    path(
        'api/user/blood_requests/<str:blood_request_id>/decrease',
        views.user_blood_request_details_decrease_unit,
        name="decrease blood request unit by 1"
    ),
    path(
        'api/user/blood_requests/<str:blood_request_id>/increase',
        views.user_blood_request_details_increase_unit,
        name="increase blood request unit by 1"
    ),
    path(
        'api/user/blood_requests/<str:blood_request_id>/delete',
        views.user_blood_request_details_delete,
        name="delete blood request"
    ),
    path(
        'api/blood_requests/',
        views.get_blood_requests,
        name="get all blood requests"
    ),
    path(
        'api/blood_request/<str:blood_request_id>/',
        views.get_blood_request_details,
        name="fetch all attributes of an blood_request"
    ),
    path(
        'api/blood_requests/<str:blood_request_id>/donate',
        views.donate_to_blood_request,
        name="donate to blood request"
    ),
    path(
        'api/blood_request/donate_draft/<str:blood_request_id>/',
        views.donate_to_blood_request_draft,
        name="donate to blood request"
    ),
    path(
        'api/blood_requests/<str:blood_request_id>/donate/validate',
        views.validate_to_blood_request,
        name="get validation for blood request"
    ),
]
