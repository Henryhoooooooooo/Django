from rest_framework.mixins import UpdateModelMixin
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, RetrieveAPIView, CreateAPIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSSerializer, BadData
from django.core import serializers
from django.conf import settings
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings
from datetime import datetime
from carts.utils import merge_cart_cookie_to_redis
from .models import User, Address
from .serializers import CreateUserSerializer, UserDetailSerializer, EmailSerializer, UserAddressSerializer, \
    AddressTitleSerializer, UserBrowserHistorySerializer, SKUSerializer
from goods.models import SKU
from rest_framework_jwt.views import ObtainJSONWebToken


class UsernameCountView(APIView):
    """
    用户名数量
    """

    def get(self, request, username):
        """
        获取指定用户名数量
        """
        # User.objects.filter(username=username)  # 判断查询集是不是空的
        # User.objects.get(username=username) # 瞅瞅会不会报错
        count = User.objects.filter(username=username).count()
        data = {
            "username": username,
            "count": count
        }
        return Response(data)


class MobileCountView(APIView):
    """
    手机号数量
    """

    def get(self, request, mobile):
        """
        获取指定手机号数量
        """
        count = User.objects.filter(mobile=mobile).count()
        data = {
            "mobile": mobile,
            "count": count
        }
        return Response(data)


# class UserView(GenericAPIView):
#     """用户注册"""
#     # 指定序列化器
#     serializer_class = CreateUserSerializer
#
#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)  # 校验  raise_exception=True直接进行“报错”  这个"报错"将会被我自动捕捉异常
#         serializer.save()
#
#         return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserView(CreateAPIView):
    """用户注册"""
    # 指定序列化器
    serializer_class = CreateUserSerializer


# GET /user/
# class UserDetailView(GenericAPIView):
#     """用户详细信息展示"""
#     serializer_class = UserDetailSerializer
#
#     def get(self, request):
#         # print(request.user)  # 如果没登录  那就是匿名用户   anonymous
#         # print(type(request.user))
#
#         serializer = self.get_serializer(instance=request.user)
#         return Response(serializer.data)


# GET /user/
class UserDetailView(RetrieveAPIView):
    """用户详细信息展示"""
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]  # 指定权限 只有用过认证的用户才能看到当前视图

    # queryset = User.objects.all()

    def get_object(self):
        """重写此方法返回， 要展示的用户模型对象"""
        return self.request.user


# PUT /email/
class EmailView(GenericAPIView):
    """修改更新用户邮箱"""
    serializer_class = EmailSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request):
        instance = request.user
        serializer = self.get_serializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


# GET /email/verification/?token=xxx
class EmailVerifyView(APIView):
    """激活用户邮箱"""

    def get(self, request):
        # 获取前端查询字符串中传入的token
        token = request.query_params.get('token')
        if not token:
            return Response({'message': '缺少token'}, status=status.HTTP_400_BAD_REQUEST)
        # 吧token进行解密  并查询对应的user
        user = User.check_verify_email_token(token)
        if user is None:
            return Response({'message': '激活失败'}, status=status.HTTP_400_BAD_REQUEST)

        # 数据库操作
        user.email_active = True
        user.save()

        # 响应
        return Response({'message': 'ok'})


class AddressViewSet(UpdateModelMixin, GenericViewSet):
    """用户收货地址 增删改查"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserAddressSerializer

    # 重写
    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    # POST /addresses/
    def create(self, request):
        """
        创建收货地址
        """
        user = request.user
        # count = user.addresses.all().count()
        count = Address.objects.filter(user=user).count()
        # 用户收货地址有上限 最多只能有20个
        if count >= 20:
            return Response({'message': '收货地址数量上限'}, status=status.HTTP_400_BAD_REQUEST)

        # 创建序列化器进行反序列化
        serializer = self.get_serializer(data=request.data)
        # 调用序列化器的is_valid() 进行校验
        serializer.is_valid(raise_exception=True)
        # 调用序列化器的save()
        serializer.save()
        # 响应
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # GET /addresses/
    def list(self, request, *args, **kwargs):
        """
        用户地址列表数据
        """
        queryset = self.get_queryset()  # get_queryset在上面进行了重写
        serializer = self.get_serializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': 20,
            'addresses': serializer.data,
        })

    # delete /addresses/<pk>/
    def destroy(self, request, *args, **kwargs):
        """
        处理删除
        """
        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    # put /addresses/pk/title/
    # 需要请求体参数 title
    @action(methods=['put'], detail=True)
    def title(self, request, pk=None):
        """
        修改标题
        """
        address = self.get_object()
        serializer = AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


    # put /addresses/pk/status/
    @action(methods=['put'], detail=True)
    def status(self, request, pk=None):
        """
        设置默认地址
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)


class UserBrowserHistoryView(CreateAPIView):
    serializer_class = UserBrowserHistorySerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        redis_conn = get_redis_connection('history')
        sku_ids = redis_conn.lrange('history_%d' % user.id, 0, -1)
        sku_list = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            sku_list.append(sku)
        serializer = SKUSerializer(sku_list, many=True)

        return Response(serializer.data)


jwt_response_payload_handler = api_settings.JWT_RESPONSE_PAYLOAD_HANDLER


class UserAuthorizerView(ObtainJSONWebToken):
    """
    用户认证
    """

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.object.get('user') or request.user
            token = serializer.object.get('token')
            response_data = jwt_response_payload_handler(token, user, request)
            response = Response(response_data)
            if api_settings.JWT_AUTH_COOKIE:
                expiration = (datetime.utcnow() +
                              api_settings.JWT_EXPIRATION_DELTA)
                response.set_cookie(api_settings.JWT_AUTH_COOKIE,
                                    token,
                                    expires=expiration,
                                    httponly=True)
            merge_cart_cookie_to_redis(request, user, response)
            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
