from functools import wraps

from django.http import JsonResponse
from rest_framework import status

def auth_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication credentials were not provided."},
                            status=status.HTTP_401_UNAUTHORIZED)

        return view_func(request, *args, **kwargs)

    return _wrapped_view