from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

# 受講者、インストラクターの情報設定
class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'student', '受講者'
        INSTRUCTOR = 'instructor', 'インストラクター'

    # 以下２つは使わないため無効化し、AbstractUser 側の username を使用する
    first_name = None
    last_name = None

    role = models.CharField(max_length=10, choices=Role.choices)
    gender = models.CharField(max_length=1, choices=[('M', '男性'), ('F', '女性')], blank=False)
    date_of_birth = models.DateField()
    phone_number = models.CharField(max_length=20)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.get_role_display()} - {self.username}"

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_instructor(self):
        return self.role == self.Role.INSTRUCTOR

# インストラクターの情報設定 (追加)
class InstructorProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='instructor_profile')

    self_introduction = models.TextField(blank=True)

    # スキル
    skill_ski = models.BooleanField(default=False)
    skill_snowboard = models.BooleanField(default=False)

    # 言語スキル
    spoken_japanese = models.BooleanField(default=False)
    spoken_english = models.BooleanField(default=False)
    spoken_chinese = models.BooleanField(default=False)
    spoken_other = models.CharField(max_length=100, blank=True)

    def clean(self):
        if self.user.role != CustomUser.Role.INSTRUCTOR:
            raise ValidationError("InstructorProfile can only be assigned to users with role 'instructor'.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"InstructorProfile for {self.user.username}"
