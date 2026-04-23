from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.top_view, name='top'),
    path('health/', views.health_check, name='health_check'),

    # 新規作成 - 受講者 - インストラクター
    path('signup/student/', views.student_signup_view, name="student_signup"),
    path('signup/instructor/', views.instructor_signup_view, name="instructor_signup"),
    # ログイン処理 - 受講者 - インストラクター
    path('login/', views.login_select_view, name="login_select"),
    path('login/student/', views.student_login_view, name="student_login"),
    path('login/instructor/', views.instructor_login_view, name="instructor_login"),
    # ログアウト
    path('logout/', views.logout_view, name="logout"),
    # ユーザー設定 - 受講者 - インストラクター
    path('student_setting/', views.student_setting, name="student_setting"),
    path('instructor_setting/', views.instructor_setting, name="instructor_setting"),
    # インストラクタープロフィール（公開）
    path('instructor/<int:user_id>/profile/', views.instructor_profile_view, name='instructor_profile'),

    # メール認証
    path('signup/done/', views.signup_done_view, name='signup_done'),
    path('activate/<str:token>/', views.activate_view, name='activate'),

    # パスワードリセット
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts_app/password_reset.html',
        email_template_name='accounts_app/password_reset_email.txt',
        subject_template_name='accounts_app/password_reset_subject.txt',
        success_url='/password-reset/done/',
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts_app/password_reset_done.html',
    ), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts_app/password_reset_confirm.html',
        success_url='/password-reset/complete/',
    ), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts_app/password_reset_complete.html',
    ), name='password_reset_complete'),

    # footer
    path('about/', views.about_view, name="about"),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('cancel_policy/', views.cancel_policy_view, name='cancel_policy'),
    path('contact/', views.contact_view, name='contact'),
]
