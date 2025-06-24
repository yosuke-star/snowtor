from django.urls import path
from . import views

urlpatterns = [
    # 新規作成 - 受講者 - インストラクター
    path('signup/student/', views.student_signup_view, name="student_signup"),
    path('signup/instructor/', views.instructor_signup_view, name="instructor_signup"),
    # ログイン処理 - 受講者 - インストラクター
    path('login/student/', views.student_login_view, name="student_login"),
    path('login/instructor/', views.instructor_login_view, name="instructor_login"),
    # ログアウト
    path('logout/', views.logout_view, name="logout"),
    # ユーザー設定 - 受講者 - インストラクター
    path('student_setting/', views.student_setting, name="student_setting"),
    path('instructor_setting/', views.instructor_setting, name="instructor_setting"),
    # footer
    path('about/', views.about_view, name="about"),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('cancel_policy/', views.cancel_policy_view, name='cancel_policy'),
    path('contact/', views.contact_view, name='contact'),
]
