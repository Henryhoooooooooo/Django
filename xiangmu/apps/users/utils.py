# !/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------
''''''


def jwt_response_payload_handler(token, user=None, request=None):
    return {
        'token': token,
        'user_id': user.id,
        'username': user.username
    }


from django.contrib.auth.backends import ModelBackend
import re
from .models import User


def get_user_by_account(account):
    try:
        if re.match(r'1[3-9]\d{9}$', account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:
        return user


class UsernameMobileAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = get_user_by_account(username)
        user.check_password(password)
        if user and user.check_password(password):
            return user
