from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Home and Analytics dashboards
    path('', views.home_dashboard, name='home_dashboard'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    
    # Shift List and CRUD
    path('shifts/', views.shift_list, name='shift_list'),
    path('shifts/create/', views.shift_create, name='shift_create'),
    path('shifts/<int:pk>/', views.shift_detail, name='shift_detail'),
    path('shifts/<int:pk>/edit/', views.shift_update, name='shift_update'),
    
    # Workflow actions
    path('shifts/<int:pk>/submit/', views.shift_submit, name='shift_submit'),
    path('shifts/<int:pk>/approve/', views.shift_approve, name='shift_approve'),
    
    # Client workflow
    path('shifts/<int:pk>/submit-to-client/', views.shift_submit_to_client, name='shift_submit_to_client'),
    path('shifts/<int:pk>/client-approve/', views.client_approve_shift, name='client_approve_shift'),
    path('client-dashboard/', views.client_dashboard, name='client_dashboard'),
    
    # Export functionality
    path('export/shifts/', views.export_shifts, name='export_shifts'),
    path('export/boq/', views.export_boq, name='export_boq'),
    path('shifts/<int:pk>/export/pdf/', views.shift_pdf_export, name='shift_pdf_export'),
]
