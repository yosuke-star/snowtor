import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count
from django.views.decorators.http import require_POST
from .decorators import instructor_required, student_required
from .forms import LessonDetailForm, LessonSearchForm
from .utils import error_response
from accounts_app.models import InstructorProfile
from .models import ActivityChoices, LessonDetail, LessonPreference, SkiResort
import stripe

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

# ダッシュボード - 受講者
@login_required
def student_dashboard_view(request):
    today = timezone.localtime().date()
    # 受講者の予約履歴を取得（未来の日付のみ表示）
    preferences = LessonPreference.objects.filter(
        student=request.user,
        lesson_detail__lesson_date__gte=timezone.now().date()
    ).select_related('lesson_detail').order_by('lesson_detail__lesson_date')

    return render(
        request,
        'dashboard_app/student_dashboard.html',
        {
            'preferences': preferences,
            'today': today,
        }
    )

# ダッシュボード - インストラクター
@login_required
def instructor_dashboard_view(request):
    today = timezone.localtime().date()
    instructor = request.user
    # インストラクターが担当し、予約されたレッスン全体（未来・過去含む）
    reservations = LessonPreference.objects.filter(
        lesson_detail__instructor=instructor
    ).select_related(
        'student',
        'lesson_detail'
    ).order_by(
        'lesson_detail__lesson_date',
        'lesson_detail__time_slot'
    )

    reservation_data = []
    for pref in reservations:
        student = pref.student
        detail = pref.lesson_detail
        reservation_data.append({
            'student_name': student.username,
            'lesson_date': detail.lesson_date,
            'time_slot': detail.time_slot_display_ja,
        })

    return render(
        request,
        'dashboard_app/instructor_dashboard.html',
        {
            'today': today,
            'reservation_data': reservation_data,
        }
    )

def _is_profile_complete(user):
    """プロフィールの必須項目（自己紹介・種目いずれか）が入力済みか確認する。"""
    try:
        profile = user.instructor_profile
    except InstructorProfile.DoesNotExist:
        return False
    return bool(profile.self_introduction) and (profile.skill_ski or profile.skill_snowboard)

@instructor_required
def instructor_schedule(request):
    profile_complete = _is_profile_complete(request.user)

    if request.method == 'POST':
        if not profile_complete:
            return error_response(request, 'レッスンを登録するには、先にプロフィールを入力してください。', status=403)
        form = LessonDetailForm(request.POST)
        if form.is_valid():
            lesson_detail = form.save(commit=False)
            lesson_detail.instructor = request.user
            lesson_detail.save()
            messages.success(request, 'レッスンを登録しました。')
            return redirect('instructor_schedule')
    else:
        form = LessonDetailForm()

    return render(request, 'dashboard_app/instructor_schedule.html', {
        'form': form,
        'profile_complete': profile_complete,
    })

# フロントの都道府県選択に応じて対応するスキー場を返すAjaxエンドポイント
@login_required
def get_ski_resorts(request):
    try:
        prefecture_id = int(request.GET.get('prefecture_id'))
    except (TypeError, ValueError):
        return JsonResponse([], safe=False)
    ski_resorts = SkiResort.objects.filter(prefecture_id=prefecture_id).values('id', 'resort_name')
    return JsonResponse(list(ski_resorts), safe=False)

# 価格取得ロジック共通化
def get_lesson_price(lesson):
    activity = lesson.activity_type.activity_name
    slot = lesson.time_slot
    if activity == ActivityChoices.SKI:
        return {
            'morning': lesson.ski_morning_price,
            'afternoon': lesson.ski_afternoon_price,
            'full_day': lesson.ski_full_day_price,
        }.get(slot)
    elif activity == ActivityChoices.SNOWBOARD:
        return {
            'morning': lesson.snowboard_morning_price,
            'afternoon': lesson.snowboard_afternoon_price,
            'full_day': lesson.snowboard_full_day_price,
        }.get(slot)
    return 0

# レッスンデータをJSONで返すビュー
@login_required
def instructor_events(request):
    lessons = LessonDetail.objects.filter(instructor=request.user)
    events = []

    for lesson in lessons:
        price = get_lesson_price(lesson)

        # カレンダーに表示させるデータを整形
        events.append({
            "title": f"¥{price}",
            "start": f"{lesson.lesson_date}T09:00:00",  # 固定 or time_slot で調整してもOK
        })

    return JsonResponse(events, safe=False)

# 受講者側がインストラクターのレッスン状況を取得する
@student_required
def lesson_search(request):

    form = LessonSearchForm(request.GET or None)
    lessons = LessonDetail.objects.none()  # デフォルトは空

    if form.is_valid():
        today = timezone.localtime().date()
        lessons = LessonDetail.objects.select_related(
            "activity_type", "instructor", "prefecture", "ski_resort"
        ).annotate(
            reserved_count=Count('lessonpreference')
        ).filter(lesson_date__gte=today)

        cd = form.cleaned_data
        if cd.get('lesson_date'):
            lessons = lessons.filter(lesson_date=cd['lesson_date'])
        if cd.get('prefecture'):
            lessons = lessons.filter(prefecture=cd['prefecture'])
        if cd.get('ski_resort'):
            lessons = lessons.filter(ski_resort=cd['ski_resort'])
        if cd.get('activity_type'):
            lessons = lessons.filter(activity_type=cd['activity_type'])
        if cd.get('level'):
            lessons = lessons.filter(level=cd['level'])
        if cd.get('lesson_type'):
            lessons = lessons.filter(lesson_type=cd['lesson_type'])
        if cd.get('time_slot'):
            lessons = lessons.filter(time_slot=cd['time_slot'])

        for lesson in lessons:
            lesson.price = get_lesson_price(lesson)
            lesson.is_full = lesson.reserved_count >= lesson.max_students

    return render(
        request,
        'dashboard_app/lesson_search.html',
        {
            'form': form,
            'lessons': lessons
        }
    )

@student_required
def lesson_confirm_view(request, lesson_id):

    lesson = get_object_or_404(LessonDetail, id=lesson_id)
    lesson.price = get_lesson_price(lesson)

    return render(
        request,
        'dashboard_app/lesson_confirm.html',
        {'lesson': lesson,}
    )

@student_required
def lesson_reserve_view(request, lesson_id):
    lesson = get_object_or_404(LessonDetail, id=lesson_id)

    # 重複予約チェック
    if LessonPreference.objects.filter(student=request.user, lesson_detail=lesson).exists():
        return redirect('lesson_history')

    # 定員チェック
    if lesson.is_at_capacity:
        return error_response(request, '定員に達しているため予約できません。')

    LessonPreference.objects.create(student=request.user, lesson_detail=lesson)
    return redirect('lesson_history')

@login_required
def lesson_history_view(request):
    preferences = LessonPreference.objects.filter(
        student=request.user).select_related(
            'lesson_detail__activity_type',
            'lesson_detail__ski_resort').order_by('-created_at')

    # 金額を含めた情報のリストをテンプレートに渡す
    history_data = []
    for pref in preferences:
        lesson = pref.lesson_detail
        price = get_lesson_price(lesson)
        history_data.append({
            'preference': pref,
            'lesson': lesson,
            'price': price,
        })

    return render(
        request,
        'dashboard_app/lesson_history.html',
        {'history_data': history_data,}
    )

@login_required
@require_POST
def lesson_cancel_view(request, preference_id):
    preference = get_object_or_404(LessonPreference, id=preference_id, student=request.user)
    preference.delete()
    return redirect('lesson_history')

@login_required
def student_events(request):
    preferences = LessonPreference.objects.filter(
        student=request.user).select_related('lesson_detail')
    events = []

    for pref in preferences:
        lesson = pref.lesson_detail
        title = f"{lesson.ski_resort.resort_name} ({lesson.get_time_slot_display()})"
        start_time = {
            "morning": "09:00:00",
            "afternoon": "13:00:00",
            "full_day": "09:00:00"
        }.get(lesson.time_slot, "09:00:00")  # デフォルトで morning に

        events.append({
            "title": title,
            "start": f"{lesson.lesson_date}T{start_time}",
        })

    return JsonResponse(events, safe=False)

@instructor_required
def instructor_history_view(request):

    lessons = LessonDetail.objects.filter(
        instructor=request.user).order_by(
            '-lesson_date').prefetch_related('lessonpreference_set__student')

    return render(
        request,
        'dashboard_app/instructor_history.html',
        {'lessons': lessons,}
    )

@require_POST
@login_required
def cancel_preference(request, pref_id):
    pref = get_object_or_404(LessonPreference, id=pref_id)

    # インストラクター本人かどうか確認
    if pref.lesson_detail.instructor != request.user:
        return error_response(request, '権限がありません。', status=403)
    # キャンセル（削除）
    pref.delete()
    return redirect('instructor_history')

@login_required
@require_POST
def cancel_lesson(request, lesson_id):
    lesson = get_object_or_404(LessonDetail, id=lesson_id)

    if lesson.instructor != request.user:
        return error_response(request, '権限がありません。', status=403)
    # 予約があればキャンセル不可にしてもいいし、今回は単純に削除
    if lesson.lessonpreference_set.exists():
        return error_response(request, '受講者がいるためキャンセルできません。')

    lesson.delete()
    return redirect('instructor_history')

@student_required
def create_checkout_session(request, lesson_id):
    lesson = get_object_or_404(LessonDetail, id=lesson_id)

    # 仮に price 属性がないときは補完しておく
    if not hasattr(lesson, 'price') or lesson.price is None:
        lesson.price = get_lesson_price(lesson)
    
    # Stripe Checkout セッション作成
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'jpy',
                'product_data': {
                    'name': f"{lesson.lesson_date}のレッスン",
                },
                'unit_amount': int(lesson.price),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(reverse('payment_success', args=[lesson.id])),
        cancel_url=request.build_absolute_uri(reverse('payment_cancel', args=[lesson.id])),
    )

    return redirect(session.url, code=303)

@student_required
def payment_success(request, lesson_id):
    lesson = get_object_or_404(LessonDetail, id=lesson_id)

    # ページ再読み込みや戻るボタンによる二重作成を防ぐ
    if LessonPreference.objects.filter(student=request.user, lesson_detail=lesson).exists():
        return render(request, 'dashboard_app/payment_success.html')

    # 定員チェック（決済後に他の受講者で埋まった場合を考慮）
    if lesson.is_at_capacity:
        return error_response(request, '定員に達しているため予約を完了できませんでした。')

    LessonPreference.objects.create(student=request.user, lesson_detail=lesson)
    logger.info(f"[PAYMENT_SUCCESS] user={request.user} lesson_id={lesson_id}")
    return render(request, 'dashboard_app/payment_success.html')

@student_required
def payment_cancel(request, lesson_id):
    logger.info(f"[PAYMENT_CANCEL] user={request.user} lesson_id={lesson_id}")
    return render(request, 'dashboard_app/payment_cancel.html')
