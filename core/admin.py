from django.contrib import admin
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from .models import Client, DrillShift, DrillingProgress, ActivityLog, MaterialUsed, ApprovalHistory, Survey, Casing

# Customize admin site
admin.site.site_header = getattr(settings, 'ADMIN_SITE_HEADER', 'Leos Investments Ltd')
admin.site.site_title = getattr(settings, 'ADMIN_SITE_TITLE', 'Leos Admin')
admin.site.index_title = getattr(settings, 'ADMIN_INDEX_TITLE', 'Daily Shift Report Administration')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email', 'phone', 'user', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'contact_person', 'email')
    ordering = ('name',)
    fieldsets = (
        ('Client Information', {
            'fields': ('name', 'contact_person', 'email', 'phone', 'address', 'is_active')
        }),
        ('User Account', {
            'fields': ('user',),
            'description': 'Link to user account for client login. Create a user first, then link here.'
        }),
    )
    raw_id_fields = ('user',)
    
    fieldsets = (
        ('Company Information', {
            'fields': ('name', 'contact_person', 'email', 'phone', 'address', 'is_active')
        }),
        ('User Account', {
            'fields': ('user',),
            'description': 'Link to user account for client login. Create user first in Users section.'
        }),
    )

    actions = ['create_or_reset_client_login']

    @admin.action(description="Create/Reset client login and show temporary password")
    def create_or_reset_client_login(self, request, queryset):
        created = 0
        updated = 0
        for client in queryset:
            # Generate a username based on client name
            base_username = slugify(client.name)[:20] or 'client'
            username = base_username
            suffix = 1
            # Find unique username if creating new
            if not client.user:
                while User.objects.filter(username=username).exists():
                    suffix += 1
                    username = f"{base_username}{suffix}"

            # Generate a secure temporary password
            temp_password = get_random_string(12)

            if client.user:
                user = client.user
                user.is_active = True
                user.set_password(temp_password)
                user.save()
                updated += 1
            else:
                user = User.objects.create_user(
                    username=username,
                    email=(client.email or ''),
                    password=temp_password,
                )
                client.user = user
                client.save(update_fields=['user'])
                created += 1

            # Ensure profile exists and is client role
            profile = getattr(user, 'profile', None)
            if profile is None:
                from accounts.models import UserProfile
                profile = UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)
            else:
                try:
                    from accounts.models import UserProfile
                    if profile.role != UserProfile.ROLE_CLIENT:
                        profile.role = UserProfile.ROLE_CLIENT
                        profile.save(update_fields=['role'])
                except Exception:
                    pass

            # Show credentials (advise password reset)
            messages.info(
                request,
                f"Credentials for {client.name}: username='{user.username}', temporary password='{temp_password}'. "
                "Ask the client to log in and change their password (or use 'Forgot password')."
            )

        if created or updated:
            messages.success(request, f"Client login accounts processed: created {created}, reset {updated}.")
        else:
            messages.warning(request, "No clients selected or no changes made.")


@admin.register(DrillShift)
class DrillShiftAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'shift_type', 'client', 'rig', 'location', 'supervisor_name', 'status', 'client_status', 'is_locked', 'created_at')
    list_filter = ('status', 'client_status', 'shift_type', 'date', 'is_locked', 'client', 'standby_client', 'standby_constructor')
    search_fields = ('rig', 'location', 'created_by__username', 'supervisor_name', 'driller_name')
    readonly_fields = ('created_at', 'updated_at', 'submitted_to_client_at', 'client_approved_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('date', 'shift_type', 'client', 'rig', 'location')
        }),
        ('Staff', {
            'fields': ('created_by', 'supervisor_name', 'driller_name', 'helper1_name', 'helper2_name', 'helper3_name', 'helper4_name')
        }),
        ('Time', {
            'fields': ('start_time', 'end_time')
        }),
        ('Standby Information', {
            'fields': (
                'standby_client', 'standby_client_reason', 'standby_client_remarks',
                'standby_constructor', 'standby_constructor_reason', 'standby_constructor_remarks'
            ),
            'classes': ('collapse',)
        }),
        ('Internal Status', {
            'fields': ('status', 'is_locked', 'notes')
        }),
        ('Client Approval', {
            'fields': ('client_status', 'client_comments', 'submitted_to_client_at', 'client_approved_at', 'client_approved_by'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DrillingProgress)
class DrillingProgressAdmin(admin.ModelAdmin):
    list_display = ('id', 'shift', 'hole_number', 'start_depth', 'end_depth', 'meters_drilled', 'recovery_percentage', 'penetration_rate')
    search_fields = ('shift__id', 'hole_number')
    readonly_fields = ('recovery_percentage', 'penetration_rate')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'shift', 'activity_type', 'duration_minutes', 'timestamp', 'performed_by')
    list_filter = ('activity_type',)


@admin.register(MaterialUsed)
class MaterialUsedAdmin(admin.ModelAdmin):
    list_display = ('id', 'shift', 'material_name', 'quantity', 'unit')


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('id', 'shift', 'survey_type', 'depth', 'dip_angle', 'azimuth', 'surveyor_name', 'survey_time')
    list_filter = ('survey_type', 'survey_time')
    search_fields = ('shift__id', 'surveyor_name')
    ordering = ('-survey_time',)


@admin.register(Casing)
class CasingAdmin(admin.ModelAdmin):
    list_display = ('id', 'shift', 'casing_size', 'casing_type', 'start_depth', 'end_depth', 'length', 'installed_at')
    list_filter = ('casing_size', 'casing_type', 'installed_at')
    search_fields = ('shift__id',)
    ordering = ('-installed_at',)


@admin.register(ApprovalHistory)
class ApprovalHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'shift', 'approver', 'role', 'decision', 'timestamp')
    list_filter = ('decision',)
