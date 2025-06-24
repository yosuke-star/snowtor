import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .forms import LessonDetailForm, LessonSearchForm
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
            'time_slot': detail.get_time_slot_display(),
        })

    return render(
        request,
        'dashboard_app/instructor_dashboard.html',
        {
            'today': today,
            'reservation_data': reservation_data,
        }
    )

@login_required
def instructor_schedule(request):
    if not request.user.is_instructor:
        return error_response(request, 'インストラクターのみアクセス可能です。')

    if request.method == 'POST':
        form = LessonDetailForm(request.POST)
        if form.is_valid():
            lesson_detail = form.save(commit=False)
            lesson_detail.instructor = request.user
            lesson_detail.save()
            return redirect('instructor_schedule')  # 登録後リダイレクト
    else:
        form = LessonDetailForm()

    return render(request, 'dashboard_app/instructor_schedule.html', {'form': form})

# フロントの都道府県選択に応じて対応するスキー場を返すAjaxエンドポイント
@login_required
def get_ski_resorts(request):
    prefecture_id = request.GET.get('prefecture_id')
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

# エラーページ表示の共通化
def error_response(request, message, status=403):
    logger.warning(f"[ERROR_RESPONSE] user={request.user} message={message}")
    return render(request, 'error.html', {'message': message}, status=status)

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
@login_required
def lesson_search(request):
    form = LessonSearchForm(request.GET or None)
    lessons = LessonDetail.objects.none()  # デフォルトは空

    if form.is_valid():
        # フォームの入力から検索条件を取得
        lesson_date = form.cleaned_data['lesson_date']
        prefecture = form.cleaned_data['prefecture']
        ski_resort = form.cleaned_data['ski_resort']
        activity_type = form.cleaned_data['activity_type']
        level = form.cleaned_data['level']
        lesson_type = form.cleaned_data['lesson_type']
        time_slot = form.cleaned_data['time_slot']

        # 厳密一致でフィルター
        lessons = LessonDetail.objects.select_related(
            "activity_type", "instructor", "prefecture", "ski_resort"
        ).filter(
            lesson_date=lesson_date,
            prefecture=prefecture,
            ski_resort=ski_resort,
            activity_type=activity_type,
            level=level,
            lesson_type=lesson_type,
            time_slot=time_slot,
        )
        for lesson in lessons:
            lesson.price = get_lesson_price(lesson)

    return render(
        request,
        'dashboard_app/lesson_search.html',
        {
            'form': form,
            'lessons': lessons
        }
    )

@login_required
def lesson_confirm_view(request, lesson_id):
    lesson = get_object_or_404(LessonDetail, id=lesson_id)
    lesson.price = get_lesson_price(lesson)

    return render(
        request,
        'dashboard_app/lesson_confirm.html',
        {'lesson': lesson,}
    )

@login_required
def lesson_reserve_view(request, lesson_id):
    lesson = get_object_or_404(LessonDetail, id=lesson_id)

    # ログインユーザーが受講者かどうか確認（念のため）
    if request.user.role != 'student':
        return redirect('lesson_search')  # インストラクターは予約できない

    # 既に予約しているかチェック（重複防止）
    existing = LessonPreference.objects.filter(student=request.user, lesson_detail=lesson)
    if existing.exists():
        # すでに予約済み → 履歴へ飛ばす（後でカスタマイズ可）
        return redirect('lesson_history')

    # 新規予約作成
    LessonPreference.objects.create(student=request.user, lesson_detail=lesson)

    # 完了ページへリダイレクト（もしくは履歴へ）
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

@login_required
def instructor_history_view(request):
    if not request.user.is_instructor:
        return error_response(request, 'インストラクターのみアクセス可能です。')

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
def cancel_lesson(request, lesson_id):
    lesson = get_object_or_404(LessonDetail, id=lesson_id)

    if lesson.instructor != request.user:
        return error_response(request, '権限がありません。', status=403)
    # 予約があればキャンセル不可にしてもいいし、今回は単純に削除
    if lesson.lessonpreference_set.exists():
        return error_response(request, '受講者がいるためキャンセルできません。')

    lesson.delete()
    return redirect('instructor_history')

@login_required
@csrf_exempt
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

@login_required
def payment_success(request, lesson_id):
    print("成功！！！！！")
    lesson = get_object_or_404(LessonDetail, id=lesson_id)
    # ここで予約をDBに保存する処理
    LessonPreference.objects.create(
        student=request.user,
        lesson_detail=lesson,
        # status='confirmed'
    )
    return render(request, 'dashboard_app/payment_success.html')

@login_required
def payment_cancel(request):
    print("キャンセル！！！！！！１")
    return render(request, 'dashboard_app/payment_cancel.html')
