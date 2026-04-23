import logging
import uuid
from accounts_app.utils import store_login_or_signup_origin_path
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from .forms import InstructorProfileForm, SignupForm, CustomPasswordChangeForm, LoginForm, UserUpdateForm
from .models import CustomUser, InstructorProfile
from django.http import HttpResponse

logger = logging.getLogger(__name__)

def health_check(request):
    return HttpResponse("OK", status=200)

def top_view(request):
    if request.user.is_authenticated:
        if request.user.is_student:
            return redirect('student_dashboard')
        elif request.user.is_instructor:
            return redirect('instructor_dashboard')
    return render(request, 'top.html')

def login_select_view(request):
    return render(request, 'accounts_app/login_select.html')

def _send_activation_email(request, user):
    token = signing.dumps({'user_id': user.pk}, salt='email-activation')
    activation_url = request.build_absolute_uri(f'/activate/{token}/')
    body = render_to_string('accounts_app/activation_email.txt', {
        'activation_url': activation_url,
    })
    send_mail(
        subject='【スノトラ】メールアドレスの確認',
        message=body,
        from_email=None,
        recipient_list=[user.email],
    )

# 新規登録処理 受講者用
def student_signup_view(request):
    store_login_or_signup_origin_path(request)
    if request.method == 'POST':
        signup_form = SignupForm(request.POST)
        if signup_form.is_valid():
            user = signup_form.save(commit=False)
            user.username = f"user_{uuid.uuid4().hex[:12]}"
            user.role = CustomUser.Role.STUDENT
            user.is_active = False
            user.save()
            _send_activation_email(request, user)
            return redirect('signup_done')
    else:
        signup_form = SignupForm()
    return render(request, 'accounts_app/student_signup.html', {'signup_form': signup_form})

# 新規登録処理 インストラクター用
def instructor_signup_view(request):
    store_login_or_signup_origin_path(request)
    if request.method == 'POST':
        signup_form = SignupForm(request.POST)
        if signup_form.is_valid():
            user = signup_form.save(commit=False)
            user.username = f"user_{uuid.uuid4().hex[:12]}"
            user.role = CustomUser.Role.INSTRUCTOR
            user.is_active = False
            user.save()
            _send_activation_email(request, user)
            return redirect('signup_done')
    else:
        signup_form = SignupForm()
    return render(request, 'accounts_app/instructor_signup.html', {'signup_form': signup_form})

def instructor_profile_view(request, user_id):
    instructor = get_object_or_404(CustomUser, id=user_id, role=CustomUser.Role.INSTRUCTOR)
    try:
        profile = instructor.instructor_profile
    except InstructorProfile.DoesNotExist:
        profile = None
    back_url = request.META.get('HTTP_REFERER', '/')
    return render(request, 'accounts_app/instructor_profile.html', {
        'instructor': instructor,
        'profile': profile,
        'back_url': back_url,
    })

def signup_done_view(request):
    return render(request, 'accounts_app/signup_done.html')

def activate_view(request, token):
    try:
        data = signing.loads(token, salt='email-activation', max_age=86400)
        user = CustomUser.objects.get(pk=data['user_id'])
    except (signing.BadSignature, signing.SignatureExpired, CustomUser.DoesNotExist):
        return render(request, 'accounts_app/activation_invalid.html')

    if not user.is_active:
        user.is_active = True
        user.save()
    return render(request, 'accounts_app/activation_done.html')

def _authenticate_by_email(request, email, password):
    """メールアドレスでユーザーを検索し認証する。"""
    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return None, None
    return authenticate(request, username=user.username, password=password), user

# ログイン処理 - 受講者側
def student_login_view(request):
    store_login_or_signup_origin_path(request)
    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            email = login_form.cleaned_data['email']
            password = login_form.cleaned_data['password']
            user, db_user = _authenticate_by_email(request, email, password)
            if user is not None:
                login(request, user)
                return redirect('student_dashboard')
            else:
                logger.warning(f"[LOGIN_FAILED] email={email}")
                if db_user and not db_user.is_active:
                    login_form.add_error(None, 'メールアドレスの確認が完了していません。届いたメールのリンクをクリックしてください。')
                else:
                    login_form.add_error(None, 'メールアドレスまたはパスワードが違います')
    else:
        login_form = LoginForm()
    return render(request, 'accounts_app/student_login.html', {'login_form': login_form})

# ログイン処理 - インストラクター側
def instructor_login_view(request):
    store_login_or_signup_origin_path(request)
    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            email = login_form.cleaned_data['email']
            password = login_form.cleaned_data['password']
            user, db_user = _authenticate_by_email(request, email, password)
            if user is not None:
                login(request, user)
                return redirect('instructor_dashboard')
            else:
                logger.warning(f"[LOGIN_FAILED] email={email}")
                if db_user and not db_user.is_active:
                    login_form.add_error(None, 'メールアドレスの確認が完了していません。届いたメールのリンクをクリックしてください。')
                else:
                    login_form.add_error(None, 'メールアドレスまたはパスワードが違います')
    else:
        login_form = LoginForm()
    return render(request, 'accounts_app/instructor_login.html', {'login_form': login_form})

# ログアウト処理
@login_required
def logout_view(request):
    # ログアウト前にユーザー情報を保存
    user = request.user
    is_student = user.is_student
    is_instructor = user.is_instructor
    # ログアウト処理
    logout(request)
    # ユーザーの条件でリダイレクトさせる
    if is_student:
        return redirect('student_login')
    elif is_instructor:
        return redirect('instructor_login')

# ユーザー情報設定 / 更新 - 受講者用
@login_required
def student_setting(request):
    if not request.user.is_student:
        messages.error(request, '受講者としてログインしてください。')
        return redirect('student_dashboard')

    # 「更新ボタン」が押された時
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)

        user_valid = user_form.is_valid()

        # パスワード欄が入力されている場合のみ検証・保存
        password_fields_filled = any([
            request.POST.get('old_password'),
            request.POST.get('new_password1'),
            request.POST.get('new_password2'),
        ])
        password_valid = password_form.is_valid() if password_fields_filled else True

        if user_valid:
            user_form.save()

        if password_fields_filled and password_valid:
            user = password_form.save()
            update_session_auth_hash(request, user)

        if not user_valid or (password_fields_filled and not password_valid):
            messages.error(request, '入力内容に誤りがあります。確認してください')
        else:
            messages.success(request, 'ユーザー情報を更新しました')
            return redirect('student_setting')
        
    user_form = UserUpdateForm(instance=request.user)
    password_form = CustomPasswordChangeForm(user=request.user)
    params = {
        'user_form': user_form,
        'password_form': password_form,
    }
    return render(request, 'accounts_app/student_setting.html', params)

# ユーザー情報設定 / 更新 - インストラクター用
@login_required
def instructor_setting(request):
    # インストラクター以外のユーザーはアクセス拒否
    if not request.user.is_instructor:
        messages.error(request, "インストラクターとしてログインしてください。")
        return redirect('instructor_dashboard')

    # ユーザーのInstructorProfileインスタンスを取得、存在しない場合は作成
    try:
        instructor_profile = request.user.instructor_profile
    except InstructorProfile.DoesNotExist:
        # プロファイルが存在しない場合は新しく作成し、保存
        instructor_profile = InstructorProfile(user=request.user)
        instructor_profile.save()

    # 「更新ボタン」が押された時
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        instructor_profile_form = InstructorProfileForm(request.POST, instance=instructor_profile)

        user_valid = user_form.is_valid()
        instructor_profile_valid = instructor_profile_form.is_valid()

        password_fields_filled = any([
            request.POST.get('old_password'),
            request.POST.get('new_password1'),
            request.POST.get('new_password2'),
        ])
        password_valid = password_form.is_valid() if password_fields_filled else True

        if user_valid and password_valid and instructor_profile_valid:
            user_form.save()
            instructor_profile_form.save()
            if password_fields_filled:
                password_form.save()
                update_session_auth_hash(request, password_form.user)
            messages.success(request, 'ユーザー情報を更新しました')
            return redirect('instructor_setting')
        else:
            messages.error(request, '入力内容に誤りがあります。確認してください')
            params = {
                'user_form': user_form,
                'password_form': password_form,
                'instructor_profile_form': instructor_profile_form,
            }
            return render(request, 'accounts_app/instructor_setting.html', params)

    else:
        # GET リクエストの場合、既存のデータでフォームを初期化する 
        user_form = UserUpdateForm(instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user)
        instructor_profile_form = InstructorProfileForm(instance=instructor_profile)
    
    # テンプレートに渡すパラメータ
    params = {
        'user_form': user_form,
        'password_form': password_form,
        'instructor_profile_form': instructor_profile_form,
    }
    return render(request, 'accounts_app/instructor_setting.html', params)

def about_view(request):
    return render(request, 'common/about.html')

def terms_view(request):
    return render(request, 'common/terms.html')

def privacy_view(request):
    return render(request, 'common/privacy.html')

def cancel_policy_view(request):
    return render(request, 'common/cancel_policy.html')

def contact_view(request):
    return render(request, 'common/contact.html')

