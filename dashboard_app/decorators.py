from functools import wraps
from django.contrib.auth.decorators import login_required
from .utils import error_response


def student_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_student:
            return error_response(request, '受講者のみアクセス可能です。')
        return view_func(request, *args, **kwargs)
    return login_required(wrapper)


def instructor_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_instructor:
            return error_response(request, 'インストラクターのみアクセス可能です。')
        return view_func(request, *args, **kwargs)
    return login_required(wrapper)
