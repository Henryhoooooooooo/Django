from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_redis import get_redis_connection
from goods.models import SKU
from decimal import Decimal
from .serializers import OrderSettlementSerializer, CommitOrderSerializer
from rest_framework.response import Response


class OrdersSettlementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        redis_conn = get_redis_connection('cart')
        cart_dict_redis = redis_conn.hgetall('cart_%d' % user.id)
        selected_ids = redis_conn.smembers('selected_%d' % user.id)
        # 定义一个字典用来保存勾选的商品及count
        cart_dict = {}  # {sku_id: count} --> {1: 2}
        # 把hash中那些勾选商品的sku_id和count取出来包装到一个新字典中
        for sku_id_bytes in selected_ids:
            cart_dict[int(sku_id_bytes)] = int(cart_dict_redis[sku_id_bytes])

        # 把勾选商品的sku模型再获取出来
        skus = SKU.objects.filter(id__in=cart_dict.keys())

        # 遍历skus 查询集取出一个一个的sku模型
        for sku in skus:
            # 给每个sku模型多定义一个count属性
            sku.count = cart_dict[sku.id]

        # 定义运费
        freight = Decimal('10.00')

        data_dict = {'freight': freight, 'skus': skus}  # 序列化时，可以对 单个模型/查询集/列表/字典 都可以进行序列化
        # 创建序列化器 进行序列化
        serializer = OrderSettlementSerializer(data_dict)
        return Response(serializer.data)

class CommitOrderView(CreateAPIView):
    """保存订单"""
    serializer_class = CommitOrderSerializer
    permission_classes = [IsAuthenticated]  # 指定权限

