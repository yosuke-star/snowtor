from django.test import TestCase
from django.urls import reverse

from accounts_app.models import CustomUser
from dashboard_app.models import ActivityType, LessonDetail, LessonPreference, Prefecture, SkiResort


class DashboardTestBase(TestCase):
    """共通のテストデータセットアップ"""
    def setUp(self):
        self.student = CustomUser.objects.create_user(
            username='student_user',
            email='student@example.com',
            password='password',
            role=CustomUser.Role.STUDENT,
            is_active=True,
        )
        self.instructor = CustomUser.objects.create_user(
            username='instructor_user',
            email='instructor@example.com',
            password='password',
            role=CustomUser.Role.INSTRUCTOR,
            is_active=True,
        )
        self.prefecture = Prefecture.objects.create(name='北海道')
        self.ski_resort = SkiResort.objects.create(resort_name='ニセコ', prefecture=self.prefecture)
        self.activity_type = ActivityType.objects.create(activity_name=1)
        self.lesson = LessonDetail.objects.create(
            lesson_date='2027-01-01',
            prefecture=self.prefecture,
            ski_resort=self.ski_resort,
            activity_type=self.activity_type,
            level='beginner',
            lesson_type='private_lesson',
            max_students=3,
            time_slot='morning',
            ski_morning_price=10000,
            instructor=self.instructor,
        )


# S-2: Stripe 系ビューのアクセス制御
class CheckoutAccessTest(DashboardTestBase):
    def test_instructor_cannot_access_checkout(self):
        self.client.force_login(self.instructor)
        response = self.client.get(
            reverse('create_checkout_session', args=[self.lesson.id])
        )
        self.assertEqual(response.status_code, 403)

    def test_instructor_cannot_access_payment_success(self):
        self.client.force_login(self.instructor)
        response = self.client.get(
            reverse('payment_success', args=[self.lesson.id])
        )
        self.assertEqual(response.status_code, 403)

    def test_instructor_cannot_access_payment_cancel(self):
        self.client.force_login(self.instructor)
        response = self.client.get(
            reverse('payment_cancel', args=[self.lesson.id])
        )
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_user_redirected_from_checkout(self):
        response = self.client.get(
            reverse('create_checkout_session', args=[self.lesson.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])


# S-3: get_ski_resorts のバリデーション
class GetSkiResortsViewTest(DashboardTestBase):
    def setUp(self):
        super().setUp()
        self.url = reverse('get_ski_resorts')
        self.client.force_login(self.student)

    def test_valid_prefecture_id_returns_resorts(self):
        response = self.client.get(self.url, {'prefecture_id': self.prefecture.id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['resort_name'], 'ニセコ')

    def test_invalid_string_returns_empty(self):
        response = self.client.get(self.url, {'prefecture_id': 'abc'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_missing_param_returns_empty(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_nonexistent_prefecture_returns_empty(self):
        response = self.client.get(self.url, {'prefecture_id': 9999})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
