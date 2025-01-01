from django.urls import path
from .views import signup, verify_phone, login, resend_verification, forgot_password, reset_password, get_my_info

urlpatterns = [
    path('signup/', signup, name='signup'),
    path('verify-phone/', verify_phone, name='verify-phone'),
    path('login/', login, name='login'),
    path('resend-verification/', resend_verification, name='resend-verification'),
    path('forgot-password/', forgot_password, name='forgot-password'),
    path('reset-password/', reset_password, name='reset-password'),
    path('get-my-info/', get_my_info, name='get-my-info'),
]
