import json

from django.contrib.auth import authenticate
from django.http import JsonResponse


from config.constant import COOKIE_NAME
from main.auth.auth_helper import get_jwt_with_user
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def login(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username=username, password=password)
    print("welcome back user" + user.username)
    if user is not None:
        token_dict = get_jwt_with_user(user)
        response = JsonResponse({"status": 200, "data": {"message": "success"}})
        response.set_cookie(COOKIE_NAME, json.dumps(token_dict), samesite='Lax', max_age=259200, httponly=True)
        return response
    else:
        return JsonResponse({"status": 401, "data": {"message": "failed"}})

@csrf_exempt
def logout(request):    
    response = JsonResponse({"status": 200, "message": "Signed Out successfully"})
    response.delete_cookie(COOKIE_NAME)
    print("logged out")
    return response
