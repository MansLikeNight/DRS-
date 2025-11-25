from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class Client(models.Model):
    """
    Client/Company model for tracking different clients.
    
    Attributes:
        name: Client company name
        user: Linked user account for client login
        contact_person: Main contact person
        email: Contact email
        phone: Contact phone number
        address: Client address
        is_active: Whether client is currently active
    """
    name = models.CharField(max_length=255, unique=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='client_profile', help_text="User account for client login")
    contact_person = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class DrillShift(models.Model):
    """
    Main model representing a drilling shift/report.
    
    A drill shift contains information about a single shift of drilling operations,
    including basic information, progress data, activities, and materials used.
    Shifts go through a workflow: draft → submitted → approved/rejected.
    
    Attributes:
        created_by: The user who created this shift report
        date: The date of the drilling shift
        rig: Name or identifier of the drilling rig
        location: Location where drilling took place
        start_time: When the shift started
        end_time: When the shift ended
        notes: Additional notes or comments
        status: Current workflow status (draft/submitted/approved/rejected)
        is_locked: Whether the shift is locked for editing
        created_at: Timestamp when the record was created
        updated_at: Timestamp when the record was last updated
    """
    STATUS_DRAFT = 'draft'
    STATUS_SUBMITTED = 'submitted'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    SHIFT_DAY = 'day'
    SHIFT_NIGHT = 'night'
    
    SHIFT_TYPE_CHOICES = [
        (SHIFT_DAY, 'Day Shift (07:00 - 19:00)'),
        (SHIFT_NIGHT, 'Night Shift (19:00 - 07:00)'),
    ]

    # Client approval status
    CLIENT_PENDING = 'pending_client'
    CLIENT_APPROVED = 'client_approved'
    CLIENT_REJECTED = 'client_rejected'
    
    CLIENT_STATUS_CHOICES = [
        (CLIENT_PENDING, 'Pending Client Approval'),
        (CLIENT_APPROVED, 'Client Approved'),
        (CLIENT_REJECTED, 'Client Rejected'),
    ]

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='shifts')
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='shifts', null=True, blank=True)
    date = models.DateField()
    shift_type = models.CharField(max_length=16, choices=SHIFT_TYPE_CHOICES, default=SHIFT_DAY)
    rig = models.CharField(max_length=128, blank=True)
    location = models.CharField(max_length=255, blank=True)

    # Project / Commercial tracking
    project_code = models.CharField(max_length=64, blank=True, help_text="Internal project or contract code")
    purchase_order_number = models.CharField(max_length=64, blank=True, help_text="Client PO / authorization reference")

    # KPI Targets (optional for off-target calculations)
    target_recovery_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Target recovery percentage for this project")
    target_rop = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Target average rate of penetration (m/hr)")
    target_meters_per_shift = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Target meters drilled per shift")
    
    # Staff information
    supervisor_name = models.CharField(max_length=255, blank=True, help_text="Shift Supervisor")
    driller_name = models.CharField(max_length=255, blank=True, help_text="Driller")
    helper1_name = models.CharField(max_length=255, blank=True, help_text="Helper 1")
    helper2_name = models.CharField(max_length=255, blank=True, help_text="Helper 2")
    helper3_name = models.CharField(max_length=255, blank=True, help_text="Helper 3")
    helper4_name = models.CharField(max_length=255, blank=True, help_text="Helper 4")
    
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)

    # Workflow timestamps
    submitted_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when shift was first submitted")
    manager_approved_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when manager approved shift")
    
    # Standby tracking
    STANDBY_CLIENT_REASONS = [
        ('pad_preparation', 'Pad Preparation'),
        ('order_by_client', 'Order by Client'),
        ('site_access', 'Site Access Issues'),
        ('client_delay', 'Client Delay'),
        ('other_client', 'Other (Client)'),
    ]
    
    STANDBY_CONSTRUCTOR_REASONS = [
        ('mobilizing', 'Mobilizing'),
        ('demobilizing', 'Demobilizing'),
        ('safety_incident', 'Safety Incident'),
        ('equipment_breakdown', 'Equipment Breakdown'),
        ('maintenance', 'Maintenance'),
        ('weather', 'Weather Conditions'),
        ('other_constructor', 'Other (Constructor)'),
    ]
    
    standby_client = models.BooleanField(default=False, help_text="Standby due to client reasons")
    standby_client_reason = models.CharField(max_length=50, choices=STANDBY_CLIENT_REASONS, blank=True)
    standby_client_remarks = models.TextField(blank=True, help_text="Additional details about client standby")
    
    standby_constructor = models.BooleanField(default=False, help_text="Standby due to constructor reasons")
    standby_constructor_reason = models.CharField(max_length=50, choices=STANDBY_CONSTRUCTOR_REASONS, blank=True)
    standby_constructor_remarks = models.TextField(blank=True, help_text="Additional details about constructor standby")
    
    # Client approval fields
    client_status = models.CharField(max_length=32, choices=CLIENT_STATUS_CHOICES, null=True, blank=True, help_text="Client approval status")
    client_comments = models.TextField(blank=True, help_text="Client feedback or rejection reason")
    submitted_to_client_at = models.DateTimeField(null=True, blank=True)
    client_approved_at = models.DateTimeField(null=True, blank=True)
    client_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='client_approvals')
    
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['status']),
            models.Index(fields=['project_code']),
        ]

    def __str__(self):
        return f"Shift {self.id} - {self.date} ({self.status})"
    
    def get_total_meters_drilled(self):
        """Calculate total meters drilled from all progress entries."""
        from django.db.models import Sum
        total = self.progress.aggregate(total=Sum('meters_drilled'))['total']
        return total or 0
    
    def get_shift_hours(self):
        """Calculate total shift duration in hours."""
        if self.start_time and self.end_time:
            from datetime import datetime, timedelta
            start = datetime.combine(self.date, self.start_time)
            end = datetime.combine(self.date, self.end_time)
            
            # Handle night shift that crosses midnight
            if end < start:
                end += timedelta(days=1)
            
            duration = end - start
            return duration.total_seconds() / 3600
        return 12  # Default 12 hours for standard shift


class DrillingProgress(models.Model):
    """
    Records drilling progress measurements for a shift.
    
    Tracks the depth measurements and drilling rate for each drilling run
    within a shift. Multiple progress records can be associated with one shift.
    
    Attributes:
        shift: The drill shift this progress belongs to
        hole_number: Hole identifier (e.g., BH-001, Hole-A)
        size: Drill bit size (PQ, HQ, NQ, etc.)
        start_depth: Starting depth in meters
        end_depth: Ending depth in meters
        meters_drilled: Total meters drilled (calculated or entered)
        core_loss: Core loss in meters
        core_gain: Core gain in meters
        recovery_percentage: Auto-calculated core recovery percentage
        penetration_rate: Drilling rate in meters per hour (auto-calculated)
        start_time: When drilling started for this segment
        end_time: When drilling ended for this segment
        remarks: Any observations or notes about this drilling segment
    """
    SIZE_CHOICES = [
        ('PQ', 'PQ (85mm)'),
        ('HQ', 'HQ (63.5mm)'),
        ('NQ', 'NQ (47.6mm)'),
        ('BQ', 'BQ (36.5mm)'),
        ('AQ', 'AQ (27mm)'),
    ]
    
    shift = models.ForeignKey(DrillShift, on_delete=models.CASCADE, related_name='progress')
    hole_number = models.CharField(max_length=50, blank=True, help_text="Hole identifier (e.g., BH-001)")
    size = models.CharField(max_length=10, choices=SIZE_CHOICES, default='HQ', help_text="Drill bit size")
    start_depth = models.DecimalField(max_digits=10, decimal_places=2)
    end_depth = models.DecimalField(max_digits=10, decimal_places=2)
    meters_drilled = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Core recovery fields
    core_loss = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Core loss in meters")
    core_gain = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Core gain in meters")
    recovery_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Auto-calculated")
    
    penetration_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Auto-calculated (m/hr)")
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    
    # Core tray image (optional)
    core_tray_image = models.ImageField(upload_to='core_trays/%Y/%m/%d/', blank=True, null=True, help_text="Photo of core tray (optional)")

    class Meta:
        ordering = ['start_depth']

    def save(self, *args, **kwargs):
        """Auto-calculate recovery percentage and penetration rate before saving."""
        # Auto-calc meters_drilled if not provided but depths are available
        try:
            if (self.meters_drilled is None or Decimal(self.meters_drilled) == 0) and \
               self.start_depth is not None and self.end_depth is not None:
                self.meters_drilled = Decimal(self.end_depth) - Decimal(self.start_depth)
        except Exception:
            # If any conversion fails, skip and let validation handle it
            pass
        # Calculate recovery percentage
        if self.meters_drilled and self.meters_drilled > 0:
            recovered_core = float(self.meters_drilled) - float(self.core_loss) + float(self.core_gain)
            self.recovery_percentage = (recovered_core / float(self.meters_drilled)) * 100
        
        # Calculate penetration rate
        if self.start_time and self.end_time and self.meters_drilled:
            from datetime import datetime, timedelta
            start = datetime.combine(datetime.today(), self.start_time)
            end = datetime.combine(datetime.today(), self.end_time)
            
            # Handle times crossing midnight
            if end < start:
                end += timedelta(days=1)
            
            duration_hours = (end - start).total_seconds() / 3600
            if duration_hours > 0:
                self.penetration_rate = float(self.meters_drilled) / duration_hours
        
        super().save(*args, **kwargs)

    def __str__(self):
        hole_info = f"{self.hole_number} - " if self.hole_number else ""
        return f"{hole_info}{self.start_depth} → {self.end_depth} ({self.meters_drilled} m)"


class ActivityLog(models.Model):
    """
    Logs activities and events that occurred during a shift.
    
    Tracks various activities like drilling operations, maintenance work,
    safety meetings, and other events with their duration and descriptions.
    
    Attributes:
        shift: The drill shift this activity belongs to
        timestamp: When the activity occurred
        activity_type: Type of activity (drilling/maintenance/safety/meeting/other)
        description: Detailed description of the activity
        duration_minutes: How long the activity took in minutes
        performed_by: User who performed or logged the activity
    """
    ACTIVITY_CHOICES = [
        ('drilling', 'Drilling'),
        ('maintenance', 'Maintenance'),
        ('safety', 'Safety'),
        ('meeting', 'Meeting'),
        ('other', 'Other'),
    ]

    shift = models.ForeignKey(DrillShift, on_delete=models.CASCADE, related_name='activities')
    timestamp = models.DateTimeField(default=timezone.now)
    activity_type = models.CharField(max_length=32, choices=ACTIVITY_CHOICES, default='other')
    description = models.TextField()
    duration_minutes = models.PositiveIntegerField(default=0, help_text="Duration in minutes (required)")
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.activity_type} @ {self.timestamp:%Y-%m-%d %H:%M}"


class MaterialUsed(models.Model):
    """
    Records materials and resources consumed during a shift.
    
    Tracks all materials used during drilling operations, including
    fuel, drilling fluids, cement, and other supplies.
    
    Attributes:
        shift: The drill shift where materials were used
        material_name: Name of the material
        quantity: Amount of material used
        unit: Unit of measurement (liters, kg, bags, etc.)
        remarks: Additional notes about material usage
    """
    shift = models.ForeignKey(DrillShift, on_delete=models.CASCADE, related_name='materials')
    material_name = models.CharField(max_length=128)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit = models.CharField(max_length=32, default='unit')
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['material_name']

    def __str__(self):
        return f"{self.material_name}: {self.quantity} {self.unit}"


class Survey(models.Model):
    """
    Records downhole/camera survey data for drill holes.
    
    Tracks survey measurements taken during drilling operations including
    orientation, dip angle, and other survey parameters.
    
    Attributes:
        shift: The drill shift when survey was conducted
        progress: Related drilling progress entry
        survey_type: Type of survey (gyro, camera, ongoing, etc.)
        depth: Depth at which survey was taken
        dip_angle: Dip angle in degrees
        azimuth: Azimuth/direction in degrees
        findings: Survey results and observations
        surveyor_name: Name of person conducting survey
        survey_time: When survey was conducted
    """
    SURVEY_TYPE_CHOICES = [
        ('gyro', 'Gyro Survey'),
        ('camera', 'Camera Survey'),
        ('ongoing', 'Ongoing Survey'),
        ('magnetic', 'Magnetic Survey'),
        ('other', 'Other'),
    ]
    
    shift = models.ForeignKey(DrillShift, on_delete=models.CASCADE, related_name='surveys')
    progress = models.ForeignKey(DrillingProgress, on_delete=models.CASCADE, related_name='surveys', null=True, blank=True)
    survey_type = models.CharField(max_length=32, choices=SURVEY_TYPE_CHOICES, default='ongoing')
    depth = models.DecimalField(max_digits=10, decimal_places=2, help_text="Depth in meters")
    dip_angle = models.DecimalField(max_digits=5, decimal_places=2, help_text="Dip angle in degrees")
    azimuth = models.DecimalField(max_digits=6, decimal_places=2, help_text="Azimuth in degrees (0-360)")
    findings = models.TextField(blank=True, help_text="Survey results and observations")
    surveyor_name = models.CharField(max_length=255, blank=True)
    survey_time = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['depth']
    
    def __str__(self):
        return f"{self.get_survey_type_display()} at {self.depth}m - Dip: {self.dip_angle}°"


class Casing(models.Model):
    """
    Records casing installation data for drill holes.
    
    Tracks casing pipes installed during drilling operations including
    size, depth, length, and type of casing used.
    
    Attributes:
        shift: The drill shift when casing was installed
        casing_size: Diameter/size of the casing (e.g., 4", 6", 8")
        casing_type: Type of casing material (PVC, Steel, etc.)
        start_depth: Starting depth of casing installation in meters
        end_depth: Ending depth of casing installation in meters
        length: Total length of casing installed in meters
        remarks: Additional notes about casing installation
        installed_at: When casing was installed
    """
    CASING_SIZE_CHOICES = [
        ('2"', '2 inch'),
        ('3"', '3 inch'),
        ('4"', '4 inch'),
        ('6"', '6 inch'),
        ('8"', '8 inch'),
        ('10"', '10 inch'),
        ('12"', '12 inch'),
    ]
    
    CASING_TYPE_CHOICES = [
        ('pvc', 'PVC'),
        ('steel', 'Steel'),
        ('hdpe', 'HDPE'),
        ('fiberglass', 'Fiberglass'),
        ('other', 'Other'),
    ]
    
    shift = models.ForeignKey(DrillShift, on_delete=models.CASCADE, related_name='casings')
    casing_size = models.CharField(max_length=10, choices=CASING_SIZE_CHOICES, help_text="Casing diameter")
    casing_type = models.CharField(max_length=32, choices=CASING_TYPE_CHOICES, default='pvc', help_text="Casing material type")
    start_depth = models.DecimalField(max_digits=10, decimal_places=2, help_text="Starting depth in meters")
    end_depth = models.DecimalField(max_digits=10, decimal_places=2, help_text="Ending depth in meters")
    length = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total length in meters")
    remarks = models.TextField(blank=True, help_text="Notes about casing installation")
    installed_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['start_depth']
    
    def __str__(self):
        return f"{self.casing_size} {self.get_casing_type_display()} - {self.start_depth}m to {self.end_depth}m"


class ApprovalHistory(models.Model):
    """
    Tracks the approval workflow history for drill shifts.
    
    Records each approval action taken on a shift, including who approved/rejected
    it, when, and any comments provided. Maintains a complete audit trail.
    
    Attributes:
        shift: The drill shift being approved
        approver: User who made the approval decision
        role: Role of the approver at time of approval
        decision: Approval decision (pending/approved/rejected)
        comments: Comments or feedback from the approver
        timestamp: When the approval action was taken
    """
    DECISION_PENDING = 'pending'
    DECISION_APPROVED = 'approved'
    DECISION_REJECTED = 'rejected'

    DECISION_CHOICES = [
        (DECISION_PENDING, 'Pending'),
        (DECISION_APPROVED, 'Approved'),
        (DECISION_REJECTED, 'Rejected'),
    ]

    shift = models.ForeignKey(DrillShift, on_delete=models.CASCADE, related_name='approvals')
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    role = models.CharField(max_length=64, blank=True)
    decision = models.CharField(max_length=16, choices=DECISION_CHOICES, default=DECISION_PENDING)
    comments = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.shift_id} - {self.decision} by {self.approver_id} @ {self.timestamp:%Y-%m-%d %H:%M}"


class Alert(models.Model):
    """
    System alerts for drilling operations requiring manager attention.
    
    Automatically generated when certain thresholds are breached:
    - Recovery below 70%
    - ROP drop > 30% vs previous shift
    - Excessive downtime (>4 hours)
    - Bit failure indicators
    
    Attributes:
        shift: Related drill shift that triggered the alert
        alert_type: Type of alert (recovery/rop_drop/downtime/bit_failure)
        severity: Alert severity level (low/medium/high/critical)
        title: Short alert title
        description: Detailed alert description
        value: Numerical value related to the alert (e.g., recovery %, ROP drop %)
        threshold: The threshold that was breached
        is_active: Whether alert is still active/unresolved
        is_acknowledged: Whether a manager has acknowledged the alert
        acknowledged_by: Manager who acknowledged the alert
        acknowledged_at: When the alert was acknowledged
        created_at: When the alert was created
    """
    ALERT_RECOVERY = 'recovery'
    ALERT_ROP_DROP = 'rop_drop'
    ALERT_DOWNTIME = 'downtime'
    ALERT_BIT_FAILURE = 'bit_failure'
    
    ALERT_TYPE_CHOICES = [
        (ALERT_RECOVERY, 'Low Core Recovery'),
        (ALERT_ROP_DROP, 'ROP Drop'),
        (ALERT_DOWNTIME, 'Excessive Downtime'),
        (ALERT_BIT_FAILURE, 'Bit Failure Warning'),
    ]
    
    SEVERITY_LOW = 'low'
    SEVERITY_MEDIUM = 'medium'
    SEVERITY_HIGH = 'high'
    SEVERITY_CRITICAL = 'critical'
    
    SEVERITY_CHOICES = [
        (SEVERITY_LOW, 'Low'),
        (SEVERITY_MEDIUM, 'Medium'),
        (SEVERITY_HIGH, 'High'),
        (SEVERITY_CRITICAL, 'Critical'),
    ]
    
    shift = models.ForeignKey(DrillShift, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=32, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default=SEVERITY_MEDIUM)
    title = models.CharField(max_length=255)
    description = models.TextField()
    value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Alert value (%, hours, etc)")
    threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Threshold breached")
    is_active = models.BooleanField(default=True)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='acknowledged_alerts')
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_type', 'is_active']),
            models.Index(fields=['severity', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.shift} ({self.get_severity_display()})"
    
    def acknowledge(self, user):
        """Mark alert as acknowledged by a manager."""
        self.is_acknowledged = True
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()
