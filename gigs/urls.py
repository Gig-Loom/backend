from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_gigs, name='get_gigs'),
    path('<int:gig_id>/', views.get_gig_by_id, name='get_gig_by_id'),
    path('create/', views.create_gig, name='create_gig'),
    path('update/<int:gig_id>/', views.update_gig, name='update_gig'),
    path('delete/<int:gig_id>/', views.delete_gig, name='delete_gig'),
]
