"""
Utility functions for BOQ/export and calculations.
Provides functionality for generating shift summaries, exporting to CSV/Excel,
and calculating drilling progress statistics.
"""

import csv
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any
import xlsxwriter
from django.db.models import Sum, Avg, F
from django.db import connection
try:
    # Window may not be available/usable on all DB backends (older SQLite)
    from django.db.models import Window
except Exception:
    Window = None
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from .models import DrillShift, DrillingProgress, MaterialUsed

def generate_shift_summary(shift: DrillShift) -> Dict[str, Any]:
    """Generate summary statistics for a single shift."""
    progress_data = shift.progress.aggregate(
        total_meters=Sum('meters_drilled'),
        avg_penetration=Avg('penetration_rate')
    )
    
    material_data = shift.materials.values('material_name').annotate(
        total_quantity=Sum('quantity')
    )
    
    return {
        'shift_id': shift.id,
        'date': shift.date,
        'location': shift.location,
        'rig': shift.rig,
        'total_meters': progress_data['total_meters'] or Decimal('0.00'),
        'avg_penetration': progress_data['avg_penetration'] or Decimal('0.00'),
        'materials': {
            item['material_name']: item['total_quantity']
            for item in material_data
        }
    }

def export_shifts_to_csv(shifts: List[DrillShift], response: HttpResponse) -> HttpResponse:
    """Export shifts data to CSV format."""
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Shift ID', 'Date', 'Location', 'Rig', 
        'Total Meters', 'Avg. Penetration Rate',
        'Status', 'Created By', 'Materials Used'
    ])
    
    # Write data rows
    for shift in shifts:
        summary = generate_shift_summary(shift)
        materials_str = ', '.join(
            f"{name}: {qty}" 
            for name, qty in summary['materials'].items()
        )
        
        writer.writerow([
            shift.id,
            shift.date.strftime('%Y-%m-%d'),
            shift.location,
            shift.rig,
            f"{summary['total_meters']:.2f}",
            f"{summary['avg_penetration']:.2f}",
            shift.get_status_display(),
            shift.created_by.username,
            materials_str
        ])
    
    return response

def export_monthly_boq(shifts: List[DrillShift], response: HttpResponse) -> HttpResponse:
    """Export monthly BOQ report to Excel."""
    workbook = xlsxwriter.Workbook(response)
    
    # Styles
    header_style = workbook.add_format({
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#4F81BD',
        'font_color': 'white',
        'border': 1
    })
    
    date_style = workbook.add_format({
        'num_format': 'yyyy-mm-dd',
        'border': 1
    })
    
    number_style = workbook.add_format({
        'num_format': '#,##0.00',
        'border': 1
    })
    
    border_style = workbook.add_format({
        'border': 1
    })
    
    # Summary Sheet
    ws_summary = workbook.add_worksheet('Summary')
    ws_summary.set_column('A:A', 12)  # Date
    ws_summary.set_column('B:B', 15)  # Location
    ws_summary.set_column('C:C', 10)  # Rig
    ws_summary.set_column('D:D', 15)  # Total Meters
    ws_summary.set_column('E:E', 20)  # Avg. Penetration
    
    # Write headers
    headers = ['Date', 'Location', 'Rig', 'Total Meters', 'Avg. Penetration']
    for col, header in enumerate(headers):
        ws_summary.write(0, col, header, header_style)
    
    # Write summary data
    row = 1
    for shift in shifts:
        summary = generate_shift_summary(shift)
        ws_summary.write_datetime(row, 0, shift.date, date_style)
        ws_summary.write(row, 1, shift.location, border_style)
        ws_summary.write(row, 2, shift.rig, border_style)
        ws_summary.write_number(row, 3, float(summary['total_meters']), number_style)
        ws_summary.write_number(row, 4, float(summary['avg_penetration']), number_style)
        row += 1
    
    # Add totals
    ws_summary.write(row, 0, 'Total', header_style)
    ws_summary.write_formula(row, 3, f'=SUM(D2:D{row})', number_style)
    ws_summary.write_formula(row, 4, f'=AVERAGE(E2:E{row})', number_style)
    
    # Materials Sheet
    ws_materials = workbook.add_worksheet('Materials')
    ws_materials.set_column('A:A', 25)  # Material Name
    ws_materials.set_column('B:B', 15)  # Total Quantity
    ws_materials.set_column('C:C', 10)  # Unit
    
    # Write headers
    material_headers = ['Material', 'Total Quantity', 'Unit']
    for col, header in enumerate(material_headers):
        ws_materials.write(0, col, header, header_style)
    
    # Aggregate materials data
    materials_summary = MaterialUsed.objects.filter(
        shift__in=shifts
    ).values(
        'material_name', 'unit'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('material_name')
    
    # Write materials data
    row = 1
    for material in materials_summary:
        ws_materials.write(row, 0, material['material_name'], border_style)
        ws_materials.write_number(row, 1, float(material['total_quantity']), number_style)
        ws_materials.write(row, 2, material['unit'], border_style)
        row += 1
    
    workbook.close()
    return response

def calculate_daily_progress(shifts: List[DrillShift]) -> Dict[str, Any]:
    """Calculate daily drilling progress statistics."""
    qs = DrillShift.objects.filter(id__in=[s.id for s in shifts]).annotate(
        date_truncated=TruncDate('date')
    ).values('date_truncated').annotate(
        total_meters=Sum('progress__meters_drilled'),
        avg_penetration=Avg('progress__penetration_rate')
    ).order_by('date_truncated')

    # SQLite (test DB) may not support advanced DB functions consistently; compute in Python
    if connection.vendor == 'sqlite' or Window is None:
        # Build simple aggregated stats in Python to avoid database-specific functions
        daily = {}
        for s in shifts:
            d = s.date
            if d not in daily:
                daily[d] = {'date_truncated': d, 'total_meters': Decimal('0.00'), 'avg_penetration_sum': Decimal('0.00'), 'count': 0}
            # sum progress meters and penetration rates
            for p in s.progress.all():
                meters = p.meters_drilled or Decimal('0.00')
                daily[d]['total_meters'] += meters
                if p.penetration_rate is not None:
                    daily[d]['avg_penetration_sum'] += p.penetration_rate
                    daily[d]['count'] += 1

        results = []
        for d in sorted(daily.keys()):
            entry = daily[d]
            avg_pen = (entry['avg_penetration_sum'] / entry['count']) if entry['count'] > 0 else Decimal('0.00')
            results.append({'date_truncated': entry['date_truncated'], 'total_meters': entry['total_meters'], 'avg_penetration': avg_pen})
        return results

    # For DBs that support window functions, annotate cumulative meters
    daily_stats = DrillShift.objects.filter(id__in=[s.id for s in shifts]).annotate(
        date_truncated=TruncDate('date')
    ).values('date_truncated').annotate(
        total_meters=Sum('progress__meters_drilled'),
        avg_penetration=Avg('progress__penetration_rate'),
        cumulative_meters=Window(
            expression=Sum('progress__meters_drilled'),
            order_by=F('date_truncated').asc(),
        )
    ).order_by('date_truncated')

    return daily_stats
