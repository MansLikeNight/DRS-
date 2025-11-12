from django import forms
from django.forms import inlineformset_factory
from .models import DrillShift, DrillingProgress, ActivityLog, MaterialUsed, Survey, Casing


class DrillShiftForm(forms.ModelForm):
    class Meta:
        model = DrillShift
        fields = ['date', 'shift_type', 'client', 'rig', 'location', 
                  'supervisor_name', 'driller_name', 'helper1_name', 'helper2_name', 'helper3_name', 'helper4_name',
                  'start_time', 'end_time', 'notes',
                  'standby_client', 'standby_client_reason', 'standby_client_remarks',
                  'standby_constructor', 'standby_constructor_reason', 'standby_constructor_remarks']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'standby_client_remarks': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Additional details about client standby'}),
            'standby_constructor_remarks': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Additional details about constructor standby'}),
        }


class DrillingProgressForm(forms.ModelForm):
    class Meta:
        model = DrillingProgress
        fields = ['hole_number', 'size', 'start_depth', 'end_depth', 'meters_drilled', 
                 'core_loss', 'core_gain', 'start_time', 'end_time', 'core_tray_image', 'remarks']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'hole_number': forms.TextInput(attrs={'placeholder': 'e.g., BH-001'}),
        }


class ActivityLogForm(forms.ModelForm):
    class Meta:
        model = ActivityLog
        fields = ['activity_type', 'description', 'duration_minutes']


class MaterialUsedForm(forms.ModelForm):
    class Meta:
        model = MaterialUsed
        fields = ['material_name', 'quantity', 'unit', 'remarks']
        widgets = {
            'unit': forms.TextInput(attrs={'style': 'min-width: 100px;', 'placeholder': 'e.g., litres, bags, kg'}),
        }


class SurveyForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = ['survey_type', 'depth', 'dip_angle', 'azimuth', 'findings', 'surveyor_name']
        widgets = {
            'surveyor_name': forms.TextInput(attrs={'placeholder': 'Surveyor name'}),
        }


class CasingForm(forms.ModelForm):
    class Meta:
        model = Casing
        fields = ['casing_size', 'casing_type', 'start_depth', 'end_depth', 'length', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Installation notes'}),
        }


# Create formsets for inline editing
DrillingProgressFormSet = inlineformset_factory(
    DrillShift, DrillingProgress,
    form=DrillingProgressForm,
    extra=1, can_delete=True,
    min_num=1, validate_min=True
)

ActivityLogFormSet = inlineformset_factory(
    DrillShift, ActivityLog,
    form=ActivityLogForm,
    extra=1, can_delete=True
)

MaterialUsedFormSet = inlineformset_factory(
    DrillShift, MaterialUsed,
    form=MaterialUsedForm,
    extra=1, can_delete=True
)

SurveyFormSet = inlineformset_factory(
    DrillShift, Survey,
    form=SurveyForm,
    extra=1, can_delete=True
)

CasingFormSet = inlineformset_factory(
    DrillShift, Casing,
    form=CasingForm,
    extra=1, can_delete=True
)
