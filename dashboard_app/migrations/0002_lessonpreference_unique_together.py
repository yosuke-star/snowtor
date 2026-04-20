from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='lessonpreference',
            unique_together={('student', 'lesson_detail')},
        ),
    ]
