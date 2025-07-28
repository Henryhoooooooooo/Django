# !/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------
''''''
from rest_framework.pagination import PageNumberPagination

class StandardResultSetPagination(PageNumberPagination):
    page_size = 2
    max_page_size = 5
    page_size_query_param = 'page_size'