from django import forms
from .models import ActivityType, LessonDetail, Prefecture, SkiResort

# 共通のCSSクラス
COMMON_INPUT_CLASS = '''
    mt-1
    block
    w-full
    px-3
    py-2
    border
    border-gray-300
    rounded-md shadow-sm
    focus:outline-none
    focus:ring-indigo-500
    focus:border-indigo-500
    sm:text-sm
'''

class LessonDetailForm(forms.ModelForm):
    prefecture = forms.ModelChoiceField(
        queryset=Prefecture.objects.all(),
        widget=forms.RadioSelect,
        empty_label=None,  # 「--------」を消す
        label="都道府県"
    )

    ski_resort = forms.ModelChoiceField(
        queryset=SkiResort.objects.all(),
        widget=forms.RadioSelect,
        empty_label=None,
        label="スキー場"
    )

    activity_type = forms.ModelChoiceField(
        queryset=ActivityType.objects.all(),
        label="アクティビティタイプ"
    )

    class Meta:
        model = LessonDetail
        exclude = ['instructor'] # instructor は除外する
        widgets = {
            'lesson_date': forms.DateInput(attrs={
                'type': 'date',
                'class': COMMON_INPUT_CLASS
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ''

        # 全フィールドに共通クラス付ける例
        for field_name, field in self.fields.items():
            # すでにclass属性があれば追加、なければ設定
            existing_classes = field.widget.attrs.get('class', '')
            classes = existing_classes + ' ' + COMMON_INPUT_CLASS if existing_classes else COMMON_INPUT_CLASS
            field.widget.attrs['class'] = classes.strip()

        # もしラジオボタンなら少し違うクラスにする例
        self.fields['prefecture'].widget.attrs['class'] = 'flex space-x-4'
        self.fields['ski_resort'].widget.attrs['class'] = 'flex space-x-4'

        # ラベル表示
        self.fields['lesson_date'].label = 'レッスン日'
        self.fields['prefecture'].label = '都道府県'
        self.fields['ski_resort'].label = 'スキー場'
        self.fields['activity_type'].label = 'アクティビティタイプ'
        self.fields['level'].label = 'レベル'
        self.fields['lesson_type'].label = 'レッスン形態'
        self.fields['max_students'].label = '最大受講人数'
        self.fields['time_slot'].label = '時間帯'

        self.fields['ski_morning_price'].label = 'スキー 午前のみの料金'
        self.fields['ski_afternoon_price'].label = 'スキー 午後のみの料金'
        self.fields['ski_full_day_price'].label = 'スキー 1日の料金'

        self.fields['snowboard_morning_price'].label = 'スノーボード 午前のみの料金'
        self.fields['snowboard_afternoon_price'].label = 'スノーボード 午後のみの料金'
        self.fields['snowboard_full_day_price'].label = 'スノーボード 1日の料金'

        # デフォルトで表示される「----」を変更する
        for field_name in ['activity_type', 'level', 'lesson_type', 'time_slot']:
            self.fields[field_name].choices = [('', '選んでください')] + list(self.fields[field_name].choices)[1:]

        # 都道府県が選択済みの場合に、その県のスキー場を表示する
        if 'prefecture' in self.data:
            try:
                prefecture_id = int(self.data.get('prefecture'))
                self.fields['ski_resort'].queryset = SkiResort.objects.filter(prefecture_id=prefecture_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['ski_resort'].queryset = SkiResort.objects.filter(prefecture=self.instance.prefecture)

# 検索フォーム
class LessonSearchForm(forms.Form):
    lesson_date = forms.DateField(
        label="レッスン日",
        widget=forms.DateInput(attrs={'type': 'date', 'class': COMMON_INPUT_CLASS})
    )

    prefecture = forms.ModelChoiceField(
        queryset=Prefecture.objects.all(),
        label="都道府県",
        widget=forms.RadioSelect(attrs={'class': 'flex space-x-4'}),
        empty_label=None
    )

    ski_resort = forms.ModelChoiceField(
        queryset=SkiResort.objects.none(),  # 選択された都道府県に応じて後で動的変更
        label="スキー場",
        widget=forms.RadioSelect(attrs={'class': 'flex space-x-4'})
    )

    activity_type = forms.ModelChoiceField(
        queryset=ActivityType.objects.all(),
        label="アクティビティ",
        widget=forms.RadioSelect(attrs={'class': 'flex space-x-4'}),
        empty_label=None
    )

    level = forms.ChoiceField(
        choices=[('', '選んでください')] + list(LessonDetail._meta.get_field('level').choices),
        label="レベル",
        widget=forms.Select(attrs={'class': COMMON_INPUT_CLASS})
    )

    lesson_type = forms.ChoiceField(
        choices=[('', '選んでください')] + list(LessonDetail._meta.get_field('lesson_type').choices),
        label="レッスン形態",
        widget=forms.Select(attrs={'class': COMMON_INPUT_CLASS})
    )

    time_slot = forms.ChoiceField(
        choices=[('', '選んでください')] + list(LessonDetail._meta.get_field('time_slot').choices),
        label="時間帯",
        widget=forms.Select(attrs={'class': COMMON_INPUT_CLASS})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'prefecture' in self.data:
            try:
                prefecture_id = int(self.data.get('prefecture'))
                self.fields['ski_resort'].queryset = SkiResort.objects.filter(prefecture_id=prefecture_id)
            except (ValueError, TypeError):
                self.fields['ski_resort'].queryset = SkiResort.objects.none()
        elif 'ski_resort' in self.data:
            try:
                ski_resort_id = int(self.data.get('ski_resort'))
                ski_resort = SkiResort.objects.get(id=ski_resort_id)
                self.fields['ski_resort'].queryset = SkiResort.objects.filter(prefecture=ski_resort.prefecture)
            except (ValueError, TypeError, SkiResort.DoesNotExist):
                self.fields['ski_resort'].queryset = SkiResort.objects.none()
        else:
            self.fields['ski_resort'].queryset = SkiResort.objects.none()