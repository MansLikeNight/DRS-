from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Avg, Q, Count, F
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, FileResponse, JsonResponse
from django.utils import timezone
from decimal import Decimal
import json
from .models import DrillShift, DrillingProgress, ActivityLog, MaterialUsed, ApprovalHistory, Client, Alert
from .forms import (DrillShiftForm, DrillingProgressFormSet, ActivityLogFormSet, 
                    MaterialUsedFormSet, SurveyFormSet, CasingFormSet)
from .utils import export_shifts_to_csv, export_monthly_boq, calculate_daily_progress
from accounts.decorators import role_required
from accounts.decorators import (
    supervisor_required, manager_required, supervisor_or_manager_required,
    can_approve_shifts
)


@login_required
def home_dashboard(request):
    """
    Manager-focused home dashboard showing high-level KPIs and alerts.
    
    Displays:
    - Total meters drilled today and this month
    - Average ROP and core recovery (last 24 hours)
    - Downtime summary by category
    - Rig performance comparison (meters per rig, last 24h)
    - Top 3 issues from recent shift comments
    - Active system alerts
    
    Returns:
        Rendered home dashboard template with KPIs and chart data
    """
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    month_start = today.replace(day=1)
    last_24h = timezone.now() - timedelta(hours=24)
    
    # KPI 1: Total meters drilled today
    meters_today = DrillingProgress.objects.filter(
        shift__date=today,
        shift__status=DrillShift.STATUS_APPROVED
    ).aggregate(total=Sum('meters_drilled'))['total'] or 0
    
    # KPI 2: Total meters this month
    meters_month = DrillingProgress.objects.filter(
        shift__date__gte=month_start,
        shift__status=DrillShift.STATUS_APPROVED
    ).aggregate(total=Sum('meters_drilled'))['total'] or 0
    
    # KPI 3: Average ROP (last 24 hours)
    avg_rop_24h = DrillingProgress.objects.filter(
        shift__date__gte=yesterday,
        shift__status=DrillShift.STATUS_APPROVED,
        penetration_rate__isnull=False
    ).aggregate(avg=Avg('penetration_rate'))['avg'] or 0
    
    # KPI 4: Average core recovery (last 24 hours)
    avg_recovery_24h = DrillingProgress.objects.filter(
        shift__date__gte=yesterday,
        shift__status=DrillShift.STATUS_APPROVED,
        recovery_percentage__isnull=False
    ).aggregate(avg=Avg('recovery_percentage'))['avg'] or 0
    
    # KPI 5: Downtime summary by category (last 24h)
    downtime_data = ActivityLog.objects.filter(
        shift__date__gte=yesterday,
        shift__status=DrillShift.STATUS_APPROVED
    ).values('activity_type').annotate(
        total_hours=Sum('duration_minutes') / 60
    ).order_by('-total_hours')
    
    # KPI 6: Rig performance comparison (last 24h)
    rig_performance = DrillingProgress.objects.filter(
        shift__date__gte=yesterday,
        shift__status=DrillShift.STATUS_APPROVED,
        shift__rig__isnull=False
    ).exclude(
        shift__rig=''
    ).values('shift__rig').annotate(
        total_meters=Sum('meters_drilled')
    ).order_by('-total_meters')[:10]  # Top 10 rigs
    
    # KPI 7: Top 3 issues from latest shifts
    recent_shifts_with_issues = DrillShift.objects.filter(
        status=DrillShift.STATUS_APPROVED,
        notes__isnull=False
    ).exclude(
        notes=''
    ).order_by('-date', '-id')[:5]
    
    top_issues = []
    for shift in recent_shifts_with_issues:
        if shift.notes and len(shift.notes.strip()) > 10:
            top_issues.append({
                'date': shift.date,
                'rig': shift.rig,
                'issue': shift.notes[:200],  # Truncate long notes
                'shift_id': shift.id
            })
            if len(top_issues) >= 3:
                break
    
    # Get active alerts (before slicing for counting)
    active_alerts_qs = Alert.objects.filter(
        is_active=True,
        is_acknowledged=False
    ).select_related('shift').order_by('-severity', '-created_at')
    
    # Count alerts by severity (before slicing)
    alert_counts = {
        'critical': active_alerts_qs.filter(severity=Alert.SEVERITY_CRITICAL).count(),
        'high': active_alerts_qs.filter(severity=Alert.SEVERITY_HIGH).count(),
        'medium': active_alerts_qs.filter(severity=Alert.SEVERITY_MEDIUM).count(),
        'low': active_alerts_qs.filter(severity=Alert.SEVERITY_LOW).count(),
    }
    
    # Get top 10 for display
    active_alerts = active_alerts_qs[:10]
    
    # Prepare chart data for Chart.js
    downtime_labels = [item['activity_type'] for item in downtime_data]
    downtime_values = [float(item['total_hours']) for item in downtime_data]
    
    # Get rig performance data separately for recovery calculation
    rig_perf_with_recovery = DrillingProgress.objects.filter(
        shift__date__gte=yesterday,
        shift__status=DrillShift.STATUS_APPROVED,
        shift__rig__isnull=False
    ).exclude(
        shift__rig=''
    ).values('shift__rig').annotate(
        total_meters=Sum('meters_drilled'),
        avg_recovery=Avg('recovery_percentage')
    ).order_by('-total_meters')[:10]
    
    rig_labels = [item['shift__rig'] for item in rig_perf_with_recovery]
    rig_values = [float(item['total_meters']) for item in rig_perf_with_recovery]
    rig_recovery = [float(item['avg_recovery']) if item['avg_recovery'] else 0 for item in rig_perf_with_recovery]
    
    # Client/Project Performance (last 30 days)
    client_performance = DrillingProgress.objects.filter(
        shift__date__gte=month_start,
        shift__status=DrillShift.STATUS_APPROVED,
        shift__client__isnull=False
    ).values('shift__client__name').annotate(
        total_meters=Sum('meters_drilled'),
        avg_recovery=Avg('recovery_percentage'),
        avg_rop=Avg('penetration_rate'),
        shift_count=Count('shift', distinct=True)
    ).order_by('-total_meters')
    
    # Location/Project performance
    location_performance = DrillingProgress.objects.filter(
        shift__date__gte=month_start,
        shift__status=DrillShift.STATUS_APPROVED,
        shift__location__isnull=False
    ).exclude(
        shift__location=''
    ).values('shift__location').annotate(
        total_meters=Sum('meters_drilled'),
        avg_recovery=Avg('recovery_percentage'),
        shift_count=Count('shift', distinct=True)
    ).order_by('-total_meters')[:10]
    
    # Workflow status metrics (this month)
    shifts_month_qs = DrillShift.objects.filter(date__gte=month_start)
    draft_count = shifts_month_qs.filter(status=DrillShift.STATUS_DRAFT).count()
    submitted_count = shifts_month_qs.filter(status=DrillShift.STATUS_SUBMITTED).count()
    approved_count = shifts_month_qs.filter(status=DrillShift.STATUS_APPROVED).count()
    rejected_count = shifts_month_qs.filter(status=DrillShift.STATUS_REJECTED).count()

    # Active clients (distinct clients with approved shifts this month)
    active_clients_count = DrillShift.objects.filter(
        date__gte=month_start,
        status=DrillShift.STATUS_APPROVED,
        client__isnull=False
    ).values('client').distinct().count()

    # Client workflow metrics (approved shifts only)
    client_pending_count = shifts_month_qs.filter(status=DrillShift.STATUS_APPROVED, client_status=DrillShift.CLIENT_PENDING).count()
    client_approved_count = shifts_month_qs.filter(status=DrillShift.STATUS_APPROVED, client_status=DrillShift.CLIENT_APPROVED).count()
    client_rejected_count = shifts_month_qs.filter(status=DrillShift.STATUS_APPROVED, client_status=DrillShift.CLIENT_REJECTED).count()

    # Off-target KPIs derived from recent alerts (high+critical active)
    off_target_alerts = Alert.objects.filter(is_active=True, severity__in=[Alert.SEVERITY_HIGH, Alert.SEVERITY_CRITICAL]).select_related('shift').order_by('-created_at')[:8]

    # Placeholder average days metrics (requires timestamps/more history) - derive from approval history if available
    from django.db.models import Min
    approvals = ApprovalHistory.objects.filter(shift__in=shifts_month_qs, decision=ApprovalHistory.DECISION_APPROVED).values('shift_id').annotate(first_approved=Min('timestamp'))
    # Map for quick lookup
    approved_map = {a['shift_id']: a['first_approved'] for a in approvals}
    days_to_approve_values = []
    for s in shifts_month_qs.filter(status=DrillShift.STATUS_APPROVED):
        ts = approved_map.get(s.id)
        if ts:
            days_to_approve_values.append((ts.date() - s.date).days)
    avg_days_to_approve = round(sum(days_to_approve_values) / len(days_to_approve_values), 1) if days_to_approve_values else 0

    context = {
        'meters_today': float(meters_today),
        'meters_month': float(meters_month),
        'avg_rop_24h': round(float(avg_rop_24h), 2),
        'avg_recovery_24h': round(float(avg_recovery_24h), 2),
        'downtime_labels': json.dumps(downtime_labels),
        'downtime_values': json.dumps(downtime_values),
        'rig_labels': json.dumps(rig_labels),
        'rig_values': json.dumps(rig_values),
        'rig_recovery': json.dumps(rig_recovery),
        'top_issues': top_issues,
        'active_alerts': active_alerts,
        'alert_counts': alert_counts,
        'total_active_alerts': active_alerts.count(),
        # Workflow metrics
        'draft_count': draft_count,
        'submitted_count': submitted_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'client_pending_count': client_pending_count,
        'client_approved_count': client_approved_count,
        'client_rejected_count': client_rejected_count,
        'avg_days_to_approve': avg_days_to_approve,
        'off_target_alerts': off_target_alerts,
        'client_performance': client_performance,
        'location_performance': location_performance,
        'active_clients_count': active_clients_count,
    }
    return render(request, 'core/home_dashboard.html', context)


@login_required
def analytics_dashboard(request):
    """
    Analytics dashboard showing 30-day trends and performance metrics.
    
    Displays trends using Chart.js:
    - Daily meters drilled (last 30 days)
    - ROP trend (last 30 days)
    - Core recovery trend (last 30 days)
    - Downtime trend (stacked by category)
    - Material usage trend
    - Bit/lifter performance (meters per bit type)
    
    Returns:
        Rendered analytics template with trend data for charts
    """
    # Calculate date range (last 30 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Allow filtering by date range
    custom_start = request.GET.get('start_date')
    custom_end = request.GET.get('end_date')
    
    if custom_start and custom_end:
        try:
            start_date = datetime.strptime(custom_start, '%Y-%m-%d').date()
            end_date = datetime.strptime(custom_end, '%Y-%m-%d').date()
        except ValueError:
            messages.warning(request, 'Invalid date format. Using default 30-day range.')
    
    # Trend 1: Daily meters drilled
    daily_meters = DrillingProgress.objects.filter(
        shift__date__range=[start_date, end_date],
        shift__status=DrillShift.STATUS_APPROVED
    ).values('shift__date').annotate(
        total_meters=Sum('meters_drilled')
    ).order_by('shift__date')
    
    # Trend 2: ROP trend (daily average)
    daily_rop = DrillingProgress.objects.filter(
        shift__date__range=[start_date, end_date],
        shift__status=DrillShift.STATUS_APPROVED,
        penetration_rate__isnull=False
    ).values('shift__date').annotate(
        avg_rop=Avg('penetration_rate')
    ).order_by('shift__date')
    
    # Trend 3: Core recovery trend (daily average)
    daily_recovery = DrillingProgress.objects.filter(
        shift__date__range=[start_date, end_date],
        shift__status=DrillShift.STATUS_APPROVED,
        recovery_percentage__isnull=False
    ).values('shift__date').annotate(
        avg_recovery=Avg('recovery_percentage')
    ).order_by('shift__date')
    
    # Trend 4: Downtime by category (grouped)
    downtime_by_category = ActivityLog.objects.filter(
        shift__date__range=[start_date, end_date],
        shift__status=DrillShift.STATUS_APPROVED,
        duration_minutes__gt=0
    ).exclude(activity_type='drilling').values('shift__date', 'activity_type').annotate(
        total_hours=Sum('duration_minutes') / 60
    ).order_by('shift__date', 'activity_type')
    
    # Trend 5: Material usage (sum by material type)
    material_usage = MaterialUsed.objects.filter(
        shift__date__range=[start_date, end_date],
        shift__status=DrillShift.STATUS_APPROVED
    ).values('material_name').annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:10]  # Top 10 materials
    
    # Trend 6: Bit performance (meters per bit size)
    bit_performance = DrillingProgress.objects.filter(
        shift__date__range=[start_date, end_date],
        shift__status=DrillShift.STATUS_APPROVED,
        size__isnull=False
    ).values('size').annotate(
        total_meters=Sum('meters_drilled'),
        avg_recovery=Avg('recovery_percentage'),
        count=Count('id')
    ).order_by('-total_meters')
    
    # Format data for Chart.js
    
    # Daily meters chart
    meters_dates = [item['shift__date'].strftime('%Y-%m-%d') for item in daily_meters]
    meters_values = [float(item['total_meters']) for item in daily_meters]
    
    # ROP trend chart
    rop_dates = [item['shift__date'].strftime('%Y-%m-%d') for item in daily_rop]
    rop_values = [float(item['avg_rop']) for item in daily_rop]
    
    # Recovery trend chart
    recovery_dates = [item['shift__date'].strftime('%Y-%m-%d') for item in daily_recovery]
    recovery_values = [float(item['avg_recovery']) for item in daily_recovery]
    
    # Downtime stacked chart - organize by activity type
    downtime_datasets = {}
    downtime_dates_set = set()
    for item in downtime_by_category:
        date_str = item['shift__date'].strftime('%Y-%m-%d')
        downtime_dates_set.add(date_str)
        activity = item['activity_type']
        if activity not in downtime_datasets:
            downtime_datasets[activity] = {}
        downtime_datasets[activity][date_str] = float(item['total_hours'])
    
    downtime_dates = sorted(list(downtime_dates_set))
    downtime_chart_data = []
    downtime_has_data = False
    for activity, data in downtime_datasets.items():
        values = [data.get(date, 0) for date in downtime_dates]
        if any(v > 0 for v in values):
            downtime_has_data = True
        downtime_chart_data.append({
            'label': activity,
            'data': values
        })

    # Aggregate totals per activity for pie/donut chart
    downtime_totals = {}
    for item in downtime_by_category:
        act = item['activity_type']
        hours = float(item['total_hours']) if item['total_hours'] else 0
        downtime_totals[act] = downtime_totals.get(act, 0) + hours

    downtime_activity_labels = list(downtime_totals.keys())
    downtime_activity_values = [round(downtime_totals[l], 2) for l in downtime_activity_labels]
    
    # Material usage chart
    material_labels = [item['material_name'] for item in material_usage]
    material_values = [float(item['total_quantity']) for item in material_usage]
    
    # Bit performance chart
    bit_labels = [item['size'] for item in bit_performance]
    bit_meters = [float(item['total_meters']) for item in bit_performance]
    bit_recovery = [float(item['avg_recovery']) if item['avg_recovery'] else 0 for item in bit_performance]

    # Monthly rig performance (current month)
    rig_month = DrillingProgress.objects.filter(
        shift__date__gte=start_date.replace(day=1),
        shift__date__lte=end_date,
        shift__status=DrillShift.STATUS_APPROVED,
        shift__rig__isnull=False
    ).exclude(shift__rig='').values('shift__rig').annotate(
        total_meters=Sum('meters_drilled'),
        avg_recovery=Avg('recovery_percentage'),
        avg_rop=Avg('penetration_rate')
    ).order_by('-total_meters')
    rig_month_labels = [r['shift__rig'] for r in rig_month]
    rig_month_meters = [float(r['total_meters']) for r in rig_month]
    rig_month_recovery = [float(r['avg_recovery']) if r['avg_recovery'] else 0 for r in rig_month]
    rig_month_rop = [float(r['avg_rop']) if r['avg_rop'] else 0 for r in rig_month]
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        # Chart data as JSON
        'meters_dates': json.dumps(meters_dates),
        'meters_values': json.dumps(meters_values),
        'rop_dates': json.dumps(rop_dates),
        'rop_values': json.dumps(rop_values),
        'recovery_dates': json.dumps(recovery_dates),
        'recovery_values': json.dumps(recovery_values),
        'downtime_dates': json.dumps(downtime_dates),
        'downtime_datasets': json.dumps(downtime_chart_data),
        'downtime_has_data': downtime_has_data,
        'downtime_activity_labels': json.dumps(downtime_activity_labels),
        'downtime_activity_values': json.dumps(downtime_activity_values),
        'material_labels': json.dumps(material_labels),
        'material_values': json.dumps(material_values),
        'bit_labels': json.dumps(bit_labels),
        'bit_meters': json.dumps(bit_meters),
        'bit_recovery': json.dumps(bit_recovery),
        'rig_month_labels': json.dumps(rig_month_labels),
        'rig_month_meters': json.dumps(rig_month_meters),
        'rig_month_recovery': json.dumps(rig_month_recovery),
        'rig_month_rop': json.dumps(rig_month_rop),
    }
    return render(request, 'core/analytics_dashboard.html', context)


@login_required
def shift_list(request):
    """
    Display a list of drill shifts grouped by machine and date (24-hour view).
    
    Shows one row per rig per date, combining day and night shifts.
    
    Applies filters based on user role:
    - Clients: Only approved shifts
    - Supervisors: Own shifts + submitted/approved shifts
    - Managers: Submitted and approved shifts
    - Superusers: All shifts
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered shift list template with grouped shifts
        
    Query Parameters:
        status: Filter shifts by status (draft/submitted/approved/rejected)
        hole_number: Filter by specific hole number
    """
    # Base queryset with optimized related data loading
    shifts = DrillShift.objects.select_related(
        'created_by',
        'created_by__profile',
        'client'
    ).prefetch_related(
        'progress',
        'activities'
    ).all()
    
    # Apply role-based filters
    if not request.user.is_superuser:
        profile = request.user.profile
        if profile.is_client:
            # Clients can only see approved shifts
            shifts = shifts.filter(status=DrillShift.STATUS_APPROVED)
        elif profile.is_supervisor:
            # Supervisors can see all shifts they created plus submitted/approved ones
            shifts = shifts.filter(
                Q(created_by=request.user) |
                Q(status__in=[DrillShift.STATUS_SUBMITTED, DrillShift.STATUS_APPROVED])
            )
        elif profile.is_manager:
            # Managers can see submitted and approved shifts
            shifts = shifts.filter(
                status__in=[DrillShift.STATUS_SUBMITTED, DrillShift.STATUS_APPROVED]
            )
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        shifts = shifts.filter(status=status)
    
    # Filter by hole number if provided
    hole_number = request.GET.get('hole_number')
    if hole_number:
        shifts = shifts.filter(progress__hole_number=hole_number).distinct()
    
    # Group shifts by date and rig (24-hour periods)
    grouped_shifts = {}
    for shift in shifts:
        key = (shift.date, shift.rig)
        if key not in grouped_shifts:
            grouped_shifts[key] = {'day': None, 'night': None, 'date': shift.date, 'rig': shift.rig, 'location': shift.location, 'client': shift.client}
        
        if shift.shift_type == 'day':
            grouped_shifts[key]['day'] = shift
        else:
            grouped_shifts[key]['night'] = shift
    
    # Convert to list and sort by date (newest first)
    shift_groups = sorted(grouped_shifts.values(), key=lambda x: x['date'], reverse=True)
    
    # Get all unique hole numbers for filter dropdown
    all_hole_numbers = DrillingProgress.objects.filter(
        hole_number__isnull=False
    ).exclude(
        hole_number=''
    ).values_list('hole_number', flat=True).distinct().order_by('hole_number')
    
    context = {
        'shift_groups': shift_groups,
        'status_choices': DrillShift.STATUS_CHOICES,
        'hole_numbers': list(all_hole_numbers),
        'selected_hole': hole_number,
    }
    return render(request, 'core/shift_list.html', context)


@login_required
def shift_detail(request, pk):
    """
    Display detailed view of a single drill shift.
    
    Shows all related data including progress, activities, materials,
    and approval history. Implements role-based access control.
    
    Args:
        request: HTTP request object
        pk: Primary key of the shift to display
        
    Returns:
        Rendered shift detail template with shift data and permissions
        
    Raises:
        Http404: If shift with given pk doesn't exist
        Redirect: If user doesn't have permission to view the shift
    """
    shift = get_object_or_404(
        DrillShift.objects.select_related('created_by')
        .prefetch_related('progress', 'activities', 'materials', 'approvals'),
        pk=pk
    )
    
    # Check permissions based on role
    profile = request.user.profile
    if not request.user.is_superuser:
        if profile.is_client and shift.status != DrillShift.STATUS_APPROVED:
            messages.error(request, 'You can only view approved shifts.')
            return redirect('core:shift_list')
        elif profile.is_supervisor and shift.created_by != request.user and shift.status == DrillShift.STATUS_DRAFT:
            messages.error(request, 'You cannot view draft shifts created by others.')
            return redirect('core:shift_list')
        elif profile.is_manager and shift.status == DrillShift.STATUS_DRAFT:
            messages.error(request, 'You cannot view draft shifts.')
            return redirect('core:shift_list')
    
    # Calculate summary data for current shift
    total_meters = shift.progress.aggregate(
        total=Sum('meters_drilled')
    )['total'] or 0
    
    # Calculate total activity hours
    total_activity_minutes = shift.activities.aggregate(
        total=Sum('duration_minutes')
    )['total'] or 0
    total_activity_hours = round(total_activity_minutes / 60, 1) if total_activity_minutes else 0
    
    # Get shift hours
    shift_hours = shift.get_shift_hours()
    
    # Calculate man hours (simplified - could be enhanced with actual crew count)
    total_man_hours = round(shift_hours * 2, 1)  # Assuming 2 people per shift, rounded to 1 decimal
    
    # Get companion shift (day/night pair for same date and rig)
    companion_shift = None
    companion_meters = 0
    companion_activity_hours = 0
    companion_man_hours = 0
    
    if shift.date and shift.rig:
        # Find the opposite shift type for the same date and rig
        opposite_shift_type = 'night' if shift.shift_type == 'day' else 'day'
        companion_shift = DrillShift.objects.filter(
            date=shift.date,
            rig=shift.rig,
            shift_type=opposite_shift_type
        ).select_related('created_by').prefetch_related('progress', 'activities').first()
        
        if companion_shift:
            # Calculate companion shift metrics
            companion_meters = companion_shift.progress.aggregate(
                total=Sum('meters_drilled')
            )['total'] or 0
            
            companion_activity_minutes = companion_shift.activities.aggregate(
                total=Sum('duration_minutes')
            )['total'] or 0
            companion_activity_hours = round(companion_activity_minutes / 60, 1) if companion_activity_minutes else 0
            
            companion_shift_hours = companion_shift.get_shift_hours()
            companion_man_hours = round(companion_shift_hours * 2, 1)
    
    # Calculate 24-hour totals
    total_24h_meters = float(total_meters) + float(companion_meters)
    total_24h_man_hours = total_man_hours + companion_man_hours
    total_24h_activity_hours = total_activity_hours + companion_activity_hours
    
    context = {
        'shift': shift,
        'companion_shift': companion_shift,  # Day or night counterpart
        'total_meters': total_meters,
        'total_man_hours': total_man_hours,
        'total_activity_hours': total_activity_hours,
        # 24-hour totals
        'total_24h_meters': total_24h_meters,
        'total_24h_man_hours': total_24h_man_hours,
        'total_24h_activity_hours': total_24h_activity_hours,
        'companion_meters': companion_meters,
        'companion_activity_hours': companion_activity_hours,
        'companion_man_hours': companion_man_hours,
        'can_edit': request.user.is_superuser or (
            profile.is_supervisor and 
            shift.created_by == request.user and 
            not shift.is_locked
        ),
        'can_submit': request.user.is_superuser or (
            profile.is_supervisor and 
            shift.created_by == request.user and 
            shift.status == DrillShift.STATUS_DRAFT
        ),
        'can_approve': request.user.is_superuser or (
            not profile.is_client and 
            shift.status == DrillShift.STATUS_SUBMITTED
        )
    }
    return render(request, 'core/shift_detail.html', context)


@supervisor_required
def shift_create(request):
    """
    Create a new drill shift with related data.
    
    Handles creation of a shift along with inline formsets for:
    - Drilling progress records
    - Activity logs
    - Material usage records
    - Survey records
    - Casing records
    
    Only supervisors can create new shifts. The shift is automatically
    assigned to the current user as creator.
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered form template (GET) or redirect to shift detail (POST success)
    """
    if request.method == 'POST':
        form = DrillShiftForm(request.POST)
        progress_formset = DrillingProgressFormSet(request.POST, request.FILES, prefix='progress')
        activity_formset = ActivityLogFormSet(request.POST, prefix='activity')
        material_formset = MaterialUsedFormSet(request.POST, prefix='material')
        survey_formset = SurveyFormSet(request.POST, prefix='survey')
        casing_formset = CasingFormSet(request.POST, prefix='casing')
        
        if (form.is_valid() and progress_formset.is_valid() 
            and activity_formset.is_valid() and material_formset.is_valid()
            and survey_formset.is_valid() and casing_formset.is_valid()):
            
            # Use transaction to ensure all saves succeed or none do
            from django.db import transaction
            try:
                with transaction.atomic():
                    shift = form.save(commit=False)
                    shift.created_by = request.user
                    shift.save()
                    
                    # Save formsets
                    progress_formset.instance = shift
                    progress_formset.save()
                    
                    activity_formset.instance = shift
                    activity_formset.save()
                    
                    material_formset.instance = shift
                    material_formset.save()
                    
                    survey_formset.instance = shift
                    survey_formset.save()
                    
                    casing_formset.instance = shift
                    casing_formset.save()
                
                messages.success(request, 'Shift created successfully.')
                return redirect('core:shift_detail', pk=shift.pk)
            except Exception as e:
                messages.error(request, f'Error saving shift: {str(e)}. Please try again.')
                # Form will re-render with data preserved
        else:
            # Show validation errors
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DrillShiftForm()
        progress_formset = DrillingProgressFormSet(prefix='progress')
        activity_formset = ActivityLogFormSet(prefix='activity')
        material_formset = MaterialUsedFormSet(prefix='material')
        survey_formset = SurveyFormSet(prefix='survey')
        casing_formset = CasingFormSet(prefix='casing')
    
    context = {
        'form': form,
        'progress_formset': progress_formset,
        'activity_formset': activity_formset,
        'material_formset': material_formset,
        'survey_formset': survey_formset,
        'casing_formset': casing_formset,
    }
    return render(request, 'core/shift_form.html', context)


@supervisor_required
def shift_update(request, pk):
    """
    Update an existing drill shift.
    
    Only the creator of a shift can update it, and only if it's not locked.
    Handles updating the shift and all related formsets.
    
    Args:
        request: HTTP request object
        pk: Primary key of the shift to update
        
    Returns:
        Rendered form template (GET) or redirect to shift detail (POST success)
        
    Raises:
        Http404: If shift with given pk doesn't exist
        Redirect: If user doesn't have permission or shift is locked
    """
    shift = get_object_or_404(DrillShift, pk=pk)
    
    # Check if the user is the creator of the shift
    if shift.created_by != request.user and not request.user.is_superuser:
        messages.error(request, 'You can only edit shifts that you created.')
        return redirect('core:shift_detail', pk=shift.pk)
    
    if shift.is_locked:
        messages.error(request, 'This shift is locked and cannot be edited.')
        return redirect('core:shift_detail', pk=shift.pk)
    
    if request.method == 'POST':
        form = DrillShiftForm(request.POST, instance=shift)
        progress_formset = DrillingProgressFormSet(
            request.POST, request.FILES, instance=shift, prefix='progress'
        )
        activity_formset = ActivityLogFormSet(
            request.POST, instance=shift, prefix='activity'
        )
        material_formset = MaterialUsedFormSet(
            request.POST, instance=shift, prefix='material'
        )
        survey_formset = SurveyFormSet(
            request.POST, instance=shift, prefix='survey'
        )
        casing_formset = CasingFormSet(
            request.POST, instance=shift, prefix='casing'
        )
        
        if (form.is_valid() and progress_formset.is_valid() 
            and activity_formset.is_valid() and material_formset.is_valid()
            and survey_formset.is_valid() and casing_formset.is_valid()):
            
            # Use transaction to ensure all updates succeed or none do
            from django.db import transaction
            try:
                with transaction.atomic():
                    form.save()
                    progress_formset.save()
                    activity_formset.save()
                    material_formset.save()
                    survey_formset.save()
                    casing_formset.save()
                
                messages.success(request, 'Shift updated successfully.')
                return redirect('core:shift_detail', pk=shift.pk)
            except Exception as e:
                messages.error(request, f'Error updating shift: {str(e)}. Please try again.')
                # Form will re-render with data preserved
        else:
            # Show validation errors
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DrillShiftForm(instance=shift)
        progress_formset = DrillingProgressFormSet(instance=shift, prefix='progress')
        activity_formset = ActivityLogFormSet(instance=shift, prefix='activity')
        material_formset = MaterialUsedFormSet(instance=shift, prefix='material')
        survey_formset = SurveyFormSet(instance=shift, prefix='survey')
        casing_formset = CasingFormSet(instance=shift, prefix='casing')
    
    context = {
        'form': form,
        'progress_formset': progress_formset,
        'activity_formset': activity_formset,
        'material_formset': material_formset,
        'survey_formset': survey_formset,
        'casing_formset': casing_formset,
        'shift': shift,
    }
    return render(request, 'core/shift_form.html', context)


@supervisor_required
def shift_submit(request, pk):
    """
    Submit a draft shift for approval.
    
    Changes shift status from draft to submitted and creates an initial
    approval history entry. Only the creator can submit their own shifts.
    
    Args:
        request: HTTP request object (must be POST)
        pk: Primary key of the shift to submit
        
    Returns:
        Redirect to shift detail page
        
    Raises:
        Http404: If shift with given pk doesn't exist
        Redirect: If user doesn't have permission or shift isn't in draft status
    """
    shift = get_object_or_404(DrillShift, pk=pk)
    
    # Check if the user is the creator of the shift
    if shift.created_by != request.user and not request.user.is_superuser:
        messages.error(request, 'You can only submit shifts that you created.')
        return redirect('core:shift_detail', pk=shift.pk)
    
    if shift.status != DrillShift.STATUS_DRAFT:
        messages.error(request, 'Only draft shifts can be submitted.')
        return redirect('core:shift_detail', pk=shift.pk)
    
    if request.method == 'POST':
        shift.status = DrillShift.STATUS_SUBMITTED
        if shift.submitted_at is None:
            shift.submitted_at = timezone.now()
        shift.save()
        
        # Create approval history entry
        ApprovalHistory.objects.create(
            shift=shift,
            approver=None,  # Will be set when approved/rejected
            role='Pending Manager Review'
        )
        
        messages.success(request, 'Shift submitted for approval.')
    
    return redirect('core:shift_detail', pk=shift.pk)


@can_approve_shifts
def shift_approve(request, pk):
    """
    Approve or reject a submitted shift.
    
    Managers and authorized supervisors can approve or reject shifts.
    Approved shifts are automatically locked to prevent further editing.
    Records the decision in approval history with comments.
    
    Args:
        request: HTTP request object (must be POST)
        pk: Primary key of the shift to approve/reject
        
    Returns:
        Redirect to shift detail page
        
    Raises:
        Http404: If shift with given pk doesn't exist
        Redirect: If shift isn't in submitted status
        
    POST Parameters:
        decision: 'approved' or 'rejected'
        comments: Optional comments about the decision
    """
    shift = get_object_or_404(DrillShift, pk=pk)
    
    if shift.status != DrillShift.STATUS_SUBMITTED:
        messages.error(request, 'Only submitted shifts can be approved/rejected.')
        return redirect('core:shift_detail', pk=shift.pk)
    
    if request.method == 'POST':
        decision = request.POST.get('decision')
        comments = request.POST.get('comments', '')
        
        if decision in [ApprovalHistory.DECISION_APPROVED, ApprovalHistory.DECISION_REJECTED]:
            shift.status = DrillShift.STATUS_APPROVED if decision == ApprovalHistory.DECISION_APPROVED else DrillShift.STATUS_REJECTED
            shift.is_locked = shift.status == DrillShift.STATUS_APPROVED
            
            # If approved and client is assigned, automatically submit to client
            if decision == ApprovalHistory.DECISION_APPROVED:
                if shift.manager_approved_at is None:
                    shift.manager_approved_at = timezone.now()
            if decision == ApprovalHistory.DECISION_APPROVED and shift.client:
                shift.client_status = DrillShift.CLIENT_PENDING
                shift.submitted_to_client_at = timezone.now()
            
            shift.save()

            # Generate alerts when shift is approved
            if shift.status == DrillShift.STATUS_APPROVED:
                from .utils import evaluate_shift_alerts
                try:
                    evaluate_shift_alerts(shift)
                except Exception as e:
                    # Non-critical: do not block approval on alert generation failure
                    messages.warning(request, f'Approved but alert evaluation failed: {e}')
            
            # Record the approval decision
            ApprovalHistory.objects.create(
                shift=shift,
                approver=request.user,
                role=request.user.profile.get_role_display(),
                decision=decision,
                comments=comments
            )
            
            if decision == ApprovalHistory.DECISION_APPROVED:
                if shift.client:
                    messages.success(request, f'Shift approved and submitted to {shift.client.name} for final approval.')
                else:
                    messages.success(request, 'Shift approved.')
            else:
                messages.success(request, 'Shift rejected.')
        else:
            messages.error(request, 'Invalid decision.')
    
    return redirect('core:shift_detail', pk=shift.pk)


@login_required
def export_shifts(request):
    """
    Export shifts to CSV format.
    
    Exports shifts visible to the current user based on their role and
    any applied filters. Supports date range filtering.
    
    Args:
        request: HTTP request object
        
    Returns:
        CSV file download response
        
    Query Parameters:
        start_date: Start date for filtering (YYYY-MM-DD format)
        end_date: End date for filtering (YYYY-MM-DD format)
        status: Filter by shift status
    """
    # Get shifts based on user role and filters
    shifts = DrillShift.objects.select_related('created_by').all()
    
    # Apply role-based filters
    if not request.user.is_superuser:
        profile = request.user.profile
        if profile.is_client:
            shifts = shifts.filter(status=DrillShift.STATUS_APPROVED)
        elif profile.is_supervisor:
            shifts = shifts.filter(
                Q(created_by=request.user) |
                Q(status__in=[DrillShift.STATUS_SUBMITTED, DrillShift.STATUS_APPROVED])
            )
        elif profile.is_manager:
            shifts = shifts.filter(
                status__in=[DrillShift.STATUS_SUBMITTED, DrillShift.STATUS_APPROVED]
            )
    
    # Apply date range filter if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            shifts = shifts.filter(date__range=[start, end])
        except ValueError:
            messages.error(request, 'Invalid date format. Use YYYY-MM-DD.')
            return redirect('core:shift_list')
    
    # Create the response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="shifts.csv"'
    
    return export_shifts_to_csv(shifts, response)


@login_required
def export_boq(request):
    """
    Export monthly Bill of Quantities (BOQ) to Excel format.
    
    Generates a comprehensive BOQ report including:
    - Daily drilling progress
    - Material usage summaries
    - Activity time breakdown
    - Total meters drilled
    
    Args:
        request: HTTP request object
        
    Returns:
        Excel file download response
        
    Query Parameters:
        start_date: Start date for filtering (YYYY-MM-DD format)
        end_date: End date for filtering (YYYY-MM-DD format)
        status: Filter by shift status
    """
    # Get shifts based on user role and filters
    shifts = DrillShift.objects.select_related('created_by').all()
    
    # Apply role-based filters
    if not request.user.is_superuser:
        profile = request.user.profile
        if profile.is_client:
            shifts = shifts.filter(status=DrillShift.STATUS_APPROVED)
        elif profile.is_supervisor:
            shifts = shifts.filter(
                Q(created_by=request.user) |
                Q(status__in=[DrillShift.STATUS_SUBMITTED, DrillShift.STATUS_APPROVED])
            )
        elif profile.is_manager:
            shifts = shifts.filter(
                status__in=[DrillShift.STATUS_SUBMITTED, DrillShift.STATUS_APPROVED]
            )
    
    # Apply date range filter if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            shifts = shifts.filter(date__range=[start, end])
        except ValueError:
            messages.error(request, 'Invalid date format. Use YYYY-MM-DD.')
            return redirect('core:shift_list')
    
    # Create the response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="monthly_boq.xlsx"'
    
    return export_monthly_boq(shifts, response)


@login_required
@role_required(['manager'])
def shift_submit_to_client(request, pk):
    """
    Submit an approved shift to client for their approval.
    Only managers can submit to clients.
    """
    shift = get_object_or_404(DrillShift, pk=pk)
    
    # Check if shift is approved by manager
    if shift.status != DrillShift.STATUS_APPROVED:
        messages.error(request, 'Only approved shifts can be submitted to clients.')
        return redirect('core:shift_detail', pk=pk)
    
    # Check if client is assigned
    if not shift.client:
        messages.error(request, 'Please assign a client to this shift before submitting.')
        return redirect('core:shift_detail', pk=pk)
    
    # Submit to client
    shift.client_status = DrillShift.CLIENT_PENDING
    shift.submitted_to_client_at = timezone.now()
    shift.save()
    
    messages.success(request, f'Shift submitted to {shift.client.name} for approval.')
    return redirect('core:shift_detail', pk=pk)


@login_required
def client_dashboard(request):
    """
    Client dashboard showing shifts submitted for their approval.
    """
    # Check if user is linked to a client
    try:
        client = request.user.client_profile
    except:
        messages.error(request, 'Your account is not linked to a client profile.')
        return redirect('core:shift_list')
    
    # Get shifts for this client
    shifts = DrillShift.objects.filter(
        client=client,
        status=DrillShift.STATUS_APPROVED  # Only show manager-approved shifts
    ).select_related('created_by', 'client').prefetch_related('progress').order_by('-date')
    
    # Filter by client status
    client_status = request.GET.get('client_status', '')
    if client_status:
        shifts = shifts.filter(client_status=client_status)
    
    # Filter by date range
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    if start_date:
        shifts = shifts.filter(date__gte=start_date)
    if end_date:
        shifts = shifts.filter(date__lte=end_date)
    
    # Calculate summary counts (treat None as pending for clients)
    all_shifts = DrillShift.objects.filter(client=client, status=DrillShift.STATUS_APPROVED)
    pending_count = all_shifts.filter(Q(client_status=DrillShift.CLIENT_PENDING) | Q(client_status__isnull=True)).count()
    approved_count = all_shifts.filter(client_status=DrillShift.CLIENT_APPROVED).count()
    rejected_count = all_shifts.filter(client_status=DrillShift.CLIENT_REJECTED).count()
    total_shifts = all_shifts.count()
    
    context = {
        'shifts': shifts,
        'client': client,
        'client_status_choices': DrillShift.CLIENT_STATUS_CHOICES,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'total_shifts': total_shifts,
    }
    return render(request, 'core/client_dashboard.html', context)


@login_required
def client_approve_shift(request, pk):
    """
    Client approves or rejects a shift with comments.
    """
    shift = get_object_or_404(DrillShift, pk=pk)
    
    # Check if user is linked to a client
    try:
        client = request.user.client_profile
    except:
        messages.error(request, 'Your account is not linked to a client profile.')
        return redirect('core:shift_list')
    
    # Check if shift belongs to this client
    if shift.client != client:
        messages.error(request, 'You can only approve shifts for your company.')
        return redirect('core:client_dashboard')
    
    # Allow approval if manager approved, even if not formally submitted
    if shift.status != DrillShift.STATUS_APPROVED:
        messages.error(request, 'Only manager-approved shifts can be decided by client.')
        return redirect('core:client_dashboard')
    
    if request.method == 'POST':
        decision = request.POST.get('decision')
        comments = request.POST.get('comments', '')
        
        if decision == 'approved':
            shift.client_status = DrillShift.CLIENT_APPROVED
            shift.client_approved_at = timezone.now()
            shift.client_approved_by = request.user
            shift.client_comments = comments
            shift.is_locked = True  # Lock after client approval
            shift.save()
            messages.success(request, 'Shift approved successfully.')
        elif decision == 'rejected':
            shift.client_status = DrillShift.CLIENT_REJECTED
            shift.client_comments = comments
            shift.is_locked = False  # Unlock for re-editing
            shift.save()
            messages.warning(request, 'Shift rejected. The team can now re-edit and resubmit.')
        else:
            messages.error(request, 'Invalid decision.')
        
        return redirect('core:client_dashboard')
    
    return redirect('core:shift_detail', pk=pk)


@login_required
def shift_pdf_export(request, pk):
    """
    Export a shift report as a receipt-style PDF.
    
    Args:
        request: HTTP request object
        pk: Primary key of the shift to export
        
    Returns:
        PDF file response
    """
    from .pdf_utils import generate_shift_pdf
    
    shift = get_object_or_404(
        DrillShift.objects.select_related('created_by', 'client')
        .prefetch_related('progress', 'activities', 'materials', 'surveys', 'casings'),
        pk=pk
    )
    
    # Check permissions - user must be creator, staff, or client with access
    if not (shift.created_by == request.user or 
            request.user.is_staff or 
            (hasattr(request.user, 'client_profile') and shift.client == request.user.client_profile)):
        messages.error(request, 'You do not have permission to export this shift.')
        return redirect('core:shift_list')
    
    # Generate PDF
    pdf_buffer = generate_shift_pdf(shift)
    
    # Create filename
    filename = f"Shift_Report_{shift.date.strftime('%Y%m%d')}_{shift.rig.replace(' ', '_')}_{shift.get_shift_type_display()}.pdf"
    
    # Return PDF response
    response = FileResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response
