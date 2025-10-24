from django.urls import path

from . import views

urlpatterns = [
    # path('', views.home, name='home'),
    # path('add',views.add, name='add'),
    path('', views.main_view, name='main_view'),
    path('login/', views.login_view, name='login'),
    path('otp_view/', views.otp_view, name='otp_view'),
    path('logout_view/', views.logout_view, name='logout'),
    path('request_new_otp/', views.request_new_otp, name='request_new_otp')
]