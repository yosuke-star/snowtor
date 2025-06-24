from django.core.validators import MinValueValidator
from django.db import models
from accounts_app.models import CustomUser

# マスターテーブル
class Prefecture(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# スキー場名
class SkiResort(models.Model):
    resort_name = models.CharField(max_length=100)
    prefecture = models.ForeignKey(Prefecture, on_delete=models.CASCADE)

    def __str__(self):
        return self.resort_name

# アクティビティタイプ ski, snowboard, etc
class ActivityChoices(models.IntegerChoices):
    SKI = 1, "スキー"
    SNOWBOARD = 2, "スノーボード"
class ActivityType(models.Model):
    activity_name = models.IntegerField(choices=ActivityChoices.choices)

    def __str__(self):
        return self.get_activity_name_display()
    
    @property
    def display_name(self):
        return self.get_activity_name_display()

# --- 出勤情報（インストラクターが作成） ---
class LessonDetail(models.Model):
    LEVEL_CHOICES = [
        ('beginner', '初心者'),
        ('intermediate', '中級者'),
        ('advanced', '上級者'),
    ]
    LESSON_TYPE_CHOICES = [
    ('private_lesson', 'プライベートレッスン'),
    ]
    TIME_SLOT_CHOICES = [
        ('morning', '午前'),
        ('afternoon', '午後'),
        ('full_day', '1日'),
    ]
    lesson_date = models.DateField()
    prefecture = models.ForeignKey(Prefecture, on_delete=models.CASCADE)
    ski_resort = models.ForeignKey(SkiResort, on_delete=models.CASCADE)
    activity_type = models.ForeignKey(ActivityType, on_delete=models.CASCADE)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPE_CHOICES)
    max_students = models.IntegerField(validators=[MinValueValidator(1)])
    time_slot = models.CharField(max_length=20, choices=TIME_SLOT_CHOICES)
    ski_morning_price = models.IntegerField(blank=True, null=True)
    ski_afternoon_price = models.IntegerField(blank=True, null=True)
    ski_full_day_price = models.IntegerField(blank=True, null=True)
    snowboard_morning_price = models.IntegerField(blank=True, null=True)
    snowboard_afternoon_price = models.IntegerField(blank=True, null=True)
    snowboard_full_day_price = models.IntegerField(blank=True, null=True)
    instructor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'instructor'})

    @property
    def level_display_ja(self):
        return dict(self.LEVEL_CHOICES).get(self.level, '未設定')
    @property
    def lesson_type_display_ja(self):
        return dict(self.LESSON_TYPE_CHOICES).get(self.lesson_type, '未設定')

    @property
    def time_slot_display_ja(self):
        return dict(self.TIME_SLOT_CHOICES).get(self.time_slot, '未設定')
    
    def __str__(self):
        return f"{self.lesson_date} - {self.instructor.username}"

# --- 受講者の予約リクエスト（LessonDetailから選択） ---
class LessonPreference(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='lesson_preferences', limit_choices_to={'role': 'student'})
    lesson_detail = models.ForeignKey(LessonDetail, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} → {self.lesson_detail}"

# 履歴
class LessonHistory(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='lesson_histories_as_student')
    instructor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='lesson_histories_as_instructor')

    lesson_date = models.DateField()
    activity_type = models.CharField(max_length=20)
    level = models.CharField(max_length=20)
    lesson_type = models.CharField(max_length=20)
    time_slot = models.CharField(max_length=20)
    price = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lesson_date} - {self.student.username} → {self.instructor.username}"
