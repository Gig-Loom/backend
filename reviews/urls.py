from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_review, name='create-review'),
]
