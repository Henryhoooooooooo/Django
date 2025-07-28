# !/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------
''''''
from . import views
from django.urls import path, re_path

urlpatterns = [
    re_path('^orders/(?P<order_id>\d+)/payment/$',views.PaymentView.as_view()),

    path('payment/status/',views.PaymentStatusView.as_view()),
]