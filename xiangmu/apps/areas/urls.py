# !/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------
''''''
from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter

urlpatterns = [
    #     path('areas/', views.AreasSerializer.as_view()),
    #     path('areas/<int:pk>', views.AreaDetailView.as_view()),
    #
]

router = DefaultRouter()
router.register('areas', views.AreaViewset, basename='ares')
urlpatterns += router.urls
