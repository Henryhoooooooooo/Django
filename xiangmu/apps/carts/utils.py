import pickle
import base64
from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request, user, response):
    """
    合并请求用户的购物车数据，将未登录保存在cookie里的保存到redis中
    遇到cookie与redis中出现相同的商品时以cookie数据为主，覆盖redis中的数据
    :param request: 用户的请求对象
    :param user: 当前登录的用户
    :param response: 响应对象，用于清楚购物车cookie
    :return:
    """
    cart_str = request.COOKIES.get('cart')
    if cart_str is None:
        return
    cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
    redis_conn = get_redis_connection('cart')
    pl = redis_conn.pipeline()

    for sku_id in cart_dict:
        pl.hset('cart_%d' % user.id, sku_id, cart_dict[sku_id]['count'])
        if cart_dict[sku_id]['selected']:
            pl.sadd('selected_%d' % user.id, sku_id)

    pl.execute()

    response.delete_cookie('cart')
    return response
