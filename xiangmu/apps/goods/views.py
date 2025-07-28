from django.shortcuts import render
from rest_framework.filters import OrderingFilter
from rest_framework.generics import GenericAPIView, ListAPIView
from .serializer import SKUSerializer, SKUIndexSerializer
from .models import SKU
from drf_haystack.viewsets import HaystackViewSet


class SKUListView(ListAPIView):
    serializer_class = SKUSerializer
    # queryset = SKU.objects
    filter_backends = [OrderingFilter]  # 排序
    ordering_fields = ('create_time', 'price', 'sales')

    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        return SKU.objects.filter(is_launched=True, category_id=category_id)


class SKUSearchViewSet(HaystackViewSet):
    index_models = [SKU]
    serializer_class = SKUIndexSerializer
