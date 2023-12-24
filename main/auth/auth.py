import json

import logging

from django.contrib.auth import authenticate
from django.http import JsonResponse

from config.constant import COOKIE_NAME
from main.auth.auth_helper import get_jwt_with_user
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger("main.auth")

@csrf_exempt
def login(request):
    logger.info(f"POST request {request.POST}")
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username=username, password=password)
    # print("welcome back user" + user.username)
    logger.info(user)
    

    if user is not None:
        token_dict = get_jwt_with_user(user)
        response = JsonResponse({"status": 200, "data": {"message": "success"}})
        response.set_cookie(COOKIE_NAME, json.dumps(token_dict), samesite='None', max_age=259200, secure=True)
        logger.info(f"User {user.username} has logged in successfully")
        return response
    else:

        logger.error(f"Login failed for user {user.username}")
        return JsonResponse({"status": 401, "data": {"message": "failed"}})
    


def logout(request):
    response = JsonResponse({"status": 200, "message": "Signed Out successfully"})
    response.delete_cookie(COOKIE_NAME)
    logger.info("User has logged out")
    return response
