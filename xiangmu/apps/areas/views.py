from django.shortcuts import render
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from .serializers import AreasSerializer, SubsSerializer
from .models import Area
from rest_framework_extensions.cache.mixins import CacheResponseMixin
from rest_framework.viewsets import ReadOnlyModelViewSet


# class AreaListView(GenericAPIView):
#     serializer_class = AreasSerializer
#     queryset = Area.objects.filter(paren=None)
#
#     def get(self, request):
#         qs = self.get_queryset()
#         serializer = self.get_serializer(instance=qs, many=True)
#         return Response(serializer.data)
#
#
# class AreaDetailView(GenericAPIView):
#     serializer_class = SubsSerializer
#     queryset = Area.objects.all()
#
#     def get(self, request, pk):
#         area = self.get_object()
#         serializer = self.get_serializer(instance=area)
#         return Response(serializer.data)


# ---------------------------------------------------------------------------

# class AreaListView(ListAPIView):
#     serializer_class = AreasSerializer
#     queryset = Area.objects.filter(parent=None)
#
#
# class AreaDetailView(RetrieveAPIView):
#     serializer_class = SubsSerializer
#     queryset = Area.objects.all()


# ---------------------------------------------------------------------------


class AreaViewset(CacheResponseMixin, ReadOnlyModelViewSet):

    def get_queryset(self):
        if self.action == 'list':
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return AreasSerializer
        else:
            return SubsSerializer
