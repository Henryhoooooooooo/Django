from django.urls import path
from . import views

urlpatterns = [
    path('orders/settlement/', views.OrdersSettlementView.as_view())


]