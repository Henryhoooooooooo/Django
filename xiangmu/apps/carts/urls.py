
from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter

urlpatterns = [
     path('carts/', views.CartView.as_view()),
]
