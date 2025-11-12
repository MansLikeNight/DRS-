from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Avg, Q
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, FileResponse
from django.utils import timezone
from .models import DrillShift, DrillingProgress, ActivityLog, MaterialUsed, ApprovalHistory, Client
from .forms import (DrillShiftForm, DrillingProgressFormSet, ActivityLogFormSet, 
                    MaterialUsedFormSet, SurveyFormSet, CasingFormSet)
from .utils import export_shifts_to_csv, export_monthly_boq, calculate_daily_progress
from accounts.decorators import role_required
from accounts.decorators import (
    supervisor_required, manager_required, supervisor_or_manager_required,
    can_approve_shifts
)


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
            if decision == ApprovalHistory.DECISION_APPROVED and shift.client:
                shift.client_status = DrillShift.CLIENT_PENDING
                shift.submitted_to_client_at = timezone.now()
            
            shift.save()
            
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
