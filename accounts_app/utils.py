# accounts_app/utils.py などに置くとよさそう
# accounts_app/utils.py
def store_login_or_signup_origin_path(request):
    if request.path.startswith('/login/') or request.path.startswith('/signup/'):
        request.session['origin_path'] = request.path

