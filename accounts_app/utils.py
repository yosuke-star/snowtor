def store_login_or_signup_origin_path(request):
    if request.path.startswith('/login/') or request.path.startswith('/signup/'):
        request.session['origin_path'] = request.path


def is_password_fields_filled(post_data):
    return any([
        post_data.get('old_password'),
        post_data.get('new_password1'),
        post_data.get('new_password2'),
    ])

