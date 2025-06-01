from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search_results, name='search_results'),
    path('places/', views.places_list, name='places_list'),
    path('bookings/', views.booking_list, name='booking_list'),
]
