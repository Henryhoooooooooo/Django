from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from .serializer import CartSerializer, CartSKUSerializer, CartDeleteSerializer
import base64
import pickle
from rest_framework.response import Response
from django_redis import get_redis_connection
from goods.models import SKU


class CartView(APIView):
    def perform_authentication(self, request):
        pass

    # 延后验证 直到第一次request.user

    def post(self, request):
        """
        添加购物车
        """
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        # 尝试对请求的用户进行验证
        try:
            user = request.user
        except Exception:
            # 验证失败，用户未登录
            user = None

        if user is not None and user.is_authenticated:
            # 用户已登录，在redis中保存
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            # 记录购物车商品数量
            pl.hincrby('cart_%s' % user.id, sku_id, count)
            # 记录购物车的勾选项
            # 勾选
            if selected:
                pl.sadd('cart_selected_%s' % user.id, sku_id)
            pl.execute()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # 用户未登录，在cookie中保存
            # {
            #     1001: { "count": 10, "selected": true},
            #     ...
            # }
            # 使用pickle序列化购物车数据，pickle操作的是bytes类型
            cart = request.COOKIES.get('cart')
            if cart is not None:
                cart = pickle.loads(base64.b64decode(cart.encode()))
            else:
                cart = {}

            sku = cart.get(sku_id)
            if sku:
                count += int(sku.get('count'))

            cart[sku_id] = {
                'count': count,
                'selected': selected
            }

            cookie_cart = base64.b64encode(pickle.dumps(cart)).decode()

            response = Response(serializer.data, status=status.HTTP_201_CREATED)

            # 设置购物车的cookie
            # 需要设置有效期，否则是临时cookie
            response.set_cookie('cart', cookie_cart)
            return response

    def get(self, request):
        """
        获取购物车
        """
        try:
            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:
            # 用户已登录，从redis中读取
            redis_conn = get_redis_connection('cart')
            redis_cart = redis_conn.hgetall('cart_%s' % user.id)
            redis_cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)
            cart = {}
            for sku_id, count in redis_cart.items():
                cart[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in redis_cart_selected
                }
        else:
            # 用户未登录，从cookie中读取
            cart = request.COOKIES.get('cart')
            if cart is not None:
                cart = pickle.loads(base64.b64decode(cart.encode()))
            else:
                cart = {}

        # 遍历处理购物车数据
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku.count = cart[sku.id]['count']
            sku.selected = cart[sku.id]['selected']

        serializer = CartSKUSerializer(skus, many=True)
        return Response(serializer.data)

    def put(self, request):
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        try:
            user = request.user
        except Exception:
            # 验证失败，用户未登录
            user = None

        if user is not None and user.is_authenticated:
            redis_conn = get_redis_connection("cart")
            pl = redis_conn.pipeline()
            pl.hset('cart_%d' % user.id, sku_id, count)
            if selected:
                pl.sadd('selected_%d' % user.id, sku_id)
            else:
                pl.srem('selected_%d' % user.id, sku_id)
            pl.execute()
            return Response(serializer.data)
        else:
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                return Response({'message': '没有购物车数据'}, status=status.HTTP_400_BAD_REQUEST)
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected,
            }
            cart_bytes = pickle.dumps(cart_dict)
            cart_str_bytes = base64.b64encode(cart_bytes)
            cart_str = cart_str_bytes.decode()
            response = Response(serializer.data)
            response.set_cookie('cart', cart_str)
            return response

    def delete(self, request):
        serializer = CartDeleteSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')

        try:
            user = request.user
        except Exception:
            # 验证失败，用户未登录
            user = None

        if user and user.is_authenticated:
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            pl.hdel('cart_%d' % user.id, sku_id)
            pl.srem('selected%d' % user.id, sku_id)

            pl.execute()
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        else:
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                return Response({'message': '没有购物车数据'}, status=status.HTTP_400_BAD_REQUEST)
            if sku_id in cart_dict:
                del cart_dict[sku_id]
            response = Response(serializer.data)
            if len(cart_dict.keys()):
                cart_bytes = pickle.dumps(cart_dict)
                cart_str_bytes = base64.b64encode(cart_bytes)
                cart_str = cart_str_bytes.decode()

                response.set_cookie('cart', cart_str)
            else:
                response.delete_cookie("cart")
            return response
