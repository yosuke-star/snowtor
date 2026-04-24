from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from accounts_app.models import CustomUser
from accounts_app.utils import is_password_fields_filled


class IsPasswordFieldsFilledTest(TestCase):
    def test_all_empty_returns_false(self):
        self.assertFalse(is_password_fields_filled({}))

    def test_old_password_only_returns_true(self):
        self.assertTrue(is_password_fields_filled({'old_password': 'pass'}))

    def test_new_password1_only_returns_true(self):
        self.assertTrue(is_password_fields_filled({'new_password1': 'pass'}))

    def test_new_password2_only_returns_true(self):
        self.assertTrue(is_password_fields_filled({'new_password2': 'pass'}))

    def test_all_filled_returns_true(self):
        self.assertTrue(is_password_fields_filled({
            'old_password': 'old',
            'new_password1': 'new',
            'new_password2': 'new',
        }))


class StudentLoginViewTest(TestCase):
    def setUp(self):
        self.student = CustomUser.objects.create_user(
            username='student_user',
            email='student@example.com',
            password='correct_password',
            role=CustomUser.Role.STUDENT,
            is_active=True,
        )
        self.url = reverse('student_login')

    def test_login_success_redirects_to_dashboard(self):
        response = self.client.post(self.url, {
            'email': 'student@example.com',
            'password': 'correct_password',
        })
        self.assertRedirects(response, reverse('student_dashboard'), fetch_redirect_response=False)

    def test_login_failure_shows_error_message(self):
        response = self.client.post(self.url, {
            'email': 'student@example.com',
            'password': 'wrong_password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'メールアドレスまたはパスワードが違います',
            response.context['login_form'].non_field_errors(),
        )

    def test_login_inactive_user_shows_activation_error(self):
        self.student.is_active = False
        self.student.save()
        response = self.client.post(self.url, {
            'email': 'student@example.com',
            'password': 'correct_password',
        })
        self.assertEqual(response.status_code, 200)
        errors = response.context['login_form'].non_field_errors()
        self.assertTrue(any('メールアドレスの確認' in e for e in errors))

    def test_login_nonexistent_email_shows_error_message(self):
        response = self.client.post(self.url, {
            'email': 'nobody@example.com',
            'password': 'some_password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'メールアドレスまたはパスワードが違います',
            response.context['login_form'].non_field_errors(),
        )


class InstructorLoginViewTest(TestCase):
    def setUp(self):
        self.instructor = CustomUser.objects.create_user(
            username='instructor_user',
            email='instructor@example.com',
            password='correct_password',
            role=CustomUser.Role.INSTRUCTOR,
            is_active=True,
        )
        self.url = reverse('instructor_login')

    def test_login_success_redirects_to_dashboard(self):
        response = self.client.post(self.url, {
            'email': 'instructor@example.com',
            'password': 'correct_password',
        })
        self.assertRedirects(response, reverse('instructor_dashboard'), fetch_redirect_response=False)

    def test_login_failure_shows_error_message(self):
        response = self.client.post(self.url, {
            'email': 'instructor@example.com',
            'password': 'wrong_password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'メールアドレスまたはパスワードが違います',
            response.context['login_form'].non_field_errors(),
        )


class StudentSignupViewTest(TestCase):
    @patch('accounts_app.views._send_activation_email')
    def test_signup_creates_student_with_correct_role(self, _mock):
        response = self.client.post(reverse('student_signup'), {
            'email': 'newstudent@example.com',
            'password1': 'testpass123!',
            'password2': 'testpass123!',
        })
        self.assertRedirects(response, reverse('signup_done'), fetch_redirect_response=False)
        user = CustomUser.objects.get(email='newstudent@example.com')
        self.assertEqual(user.role, CustomUser.Role.STUDENT)
        self.assertFalse(user.is_active)

    @patch('accounts_app.views._send_activation_email')
    def test_signup_creates_instructor_with_correct_role(self, _mock):
        response = self.client.post(reverse('instructor_signup'), {
            'email': 'newinstructor@example.com',
            'password1': 'testpass123!',
            'password2': 'testpass123!',
        })
        self.assertRedirects(response, reverse('signup_done'), fetch_redirect_response=False)
        user = CustomUser.objects.get(email='newinstructor@example.com')
        self.assertEqual(user.role, CustomUser.Role.INSTRUCTOR)
        self.assertFalse(user.is_active)

    @patch('accounts_app.views._send_activation_email')
    def test_signup_invalid_form_rerenders(self, _mock):
        response = self.client.post(reverse('student_signup'), {
            'email': 'bad-email',
            'password1': 'pass',
            'password2': 'different',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(email='bad-email').exists())


class StudentSettingViewTest(TestCase):
    def setUp(self):
        self.student = CustomUser.objects.create_user(
            username='student_user',
            email='student@example.com',
            password='current_password',
            role=CustomUser.Role.STUDENT,
            is_active=True,
        )
        self.client.force_login(self.student)
        self.url = reverse('student_setting')

    def _post_data(self, **kwargs):
        data = {
            'username': 'student_user',
            'email': 'student@example.com',
        }
        data.update(kwargs)
        return data

    def test_get_renders_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('user_form', response.context)
        self.assertIn('password_form', response.context)

    def test_update_username_success(self):
        response = self.client.post(self.url, self._post_data(username='new_name'))
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.student.refresh_from_db()
        self.assertEqual(self.student.username, 'new_name')

    def test_error_preserves_posted_input(self):
        # パスワード間違いでエラーを起こし、username の入力値が残ることを確認
        response = self.client.post(self.url, self._post_data(
            username='テスト太郎',
            old_password='wrong_password',
            new_password1='NewPass123!',
            new_password2='NewPass123!',
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user_form']['username'].value(), 'テスト太郎')

    def test_error_does_not_partial_save_user(self):
        # パスワードエラー時にユーザー情報も保存されないこと
        response = self.client.post(self.url, self._post_data(
            username='テスト太郎',
            old_password='wrong_password',
            new_password1='NewPass123!',
            new_password2='NewPass123!',
        ))
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertEqual(self.student.username, 'student_user')

    def test_password_change_success(self):
        response = self.client.post(self.url, self._post_data(
            old_password='current_password',
            new_password1='NewSecurePass123!',
            new_password2='NewSecurePass123!',
        ))
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password('NewSecurePass123!'))

    def test_wrong_old_password_does_not_change_password(self):
        response = self.client.post(self.url, self._post_data(
            old_password='wrong_password',
            new_password1='NewSecurePass123!',
            new_password2='NewSecurePass123!',
        ))
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password('current_password'))

    def test_empty_password_fields_skips_password_validation(self):
        # パスワード欄が空でもユーザー情報は保存できる
        response = self.client.post(self.url, self._post_data(username='no_pw_change'))
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.student.refresh_from_db()
        self.assertEqual(self.student.username, 'no_pw_change')
