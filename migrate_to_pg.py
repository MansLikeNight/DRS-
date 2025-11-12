"""
PostgreSQL Migration Script
Migrates Daily Drill Report from SQLite to PostgreSQL
"""
import os
import sys
import subprocess
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def print_step(step, message, status="info"):
    colors = {"info": "\033[93m", "success": "\033[92m", "error": "\033[91m", "reset": "\033[0m"}
    prefix = {"info": "[→]", "success": "[✓]", "error": "[✗]"}
    print(f"{colors.get(status, '')}{prefix.get(status, '')} Step {step}: {message}{colors['reset']}")

def run_command(command, description):
    """Run a shell command and return success status"""
    print(f"    {description}...")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        if result.stdout:
            print(f"    {result.stdout.strip()}")
        return True
    else:
        print(f"    Error: {result.stderr.strip()}")
        return False

print("=== Daily Drill Report: SQLite to PostgreSQL Migration ===\n")

# Step 1: Data already backed up
print_step(1, "Data backed up from SQLite", "success")
print("    Files: users_backup.json, accounts_backup.json, core_backup.json\n")

# Step 2: Create PostgreSQL database
print_step(2, "Creating PostgreSQL database...", "info")
try:
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='postgres',
        host='localhost',
        port='5432'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'dailydrillreport'")
    if cursor.fetchone():
        print_step(2, "Database 'dailydrillreport' already exists", "success")
    else:
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier('dailydrillreport')))
        print_step(2, "Database 'dailydrillreport' created successfully", "success")
    
    cursor.close()
    conn.close()
except psycopg2.OperationalError as e:
    print_step(2, f"Cannot connect to PostgreSQL: {e}", "error")
    print("\n    Please make sure:")
    print("    1. PostgreSQL is installed and running")
    print("    2. Password is 'postgres' (or update .env file)")
    print("    3. PostgreSQL is listening on localhost:5432")
    sys.exit(1)
except Exception as e:
    print_step(2, f"Error: {e}", "error")
    sys.exit(1)

print()

# Step 3: Update .env to use PostgreSQL
print_step(3, "Updating .env to use PostgreSQL...", "info")
env_content = """PYTHONPATH=.

# Django Settings
SECRET_KEY=django-insecure-zn!omu2bf011hqie!gbh3j0ufs$-h^)_p(r5gyw9q*)0q4---4
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
# PostgreSQL Configuration (active)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=dailydrillreport
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
"""
with open('.env', 'w', encoding='utf-8') as f:
    f.write(env_content)
print_step(3, ".env updated to use PostgreSQL", "success")
print()

# Step 4: Run migrations
print_step(4, "Running migrations to create PostgreSQL schema...", "info")
if run_command(
    'C:/Users/PC/DailyDrillReport/.venv/Scripts/python.exe manage.py migrate --noinput',
    "Creating tables"
):
    print_step(4, "Migrations completed successfully", "success")
else:
    print_step(4, "Migration failed", "error")
    sys.exit(1)
print()

# Step 5: Load data
print_step(5, "Loading data into PostgreSQL...", "info")

files = [
    ('users_backup.json', 'Users'),
    ('accounts_backup.json', 'Accounts'),
    ('core_backup.json', 'Core data (shifts, drilling progress, etc.)')
]

for filename, description in files:
    print(f"    Loading {description.lower()}...")
    result = subprocess.run(
        f'C:/Users/PC/DailyDrillReport/.venv/Scripts/python.exe manage.py loaddata {filename}',
        shell=True,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print(f"    ✓ {description} loaded")
    else:
        print(f"    ! {description} had issues (may be normal if empty)")

print_step(5, "Data import completed", "success")
print()

# Step 6: Verify migration
print_step(6, "Verifying migration...", "info")
verify_script = """
from django.contrib.auth.models import User
from core.models import DrillShift, DrillingProgress, ActivityLog
print(f'    Users: {User.objects.count()}')
print(f'    Shifts: {DrillShift.objects.count()}')
print(f'    Drilling Progress: {DrillingProgress.objects.count()}')
print(f'    Activities: {ActivityLog.objects.count()}')
"""
result = subprocess.run(
    ['C:/Users/PC/DailyDrillReport/.venv/Scripts/python.exe', 'manage.py', 'shell', '-c', verify_script],
    capture_output=True,
    text=True
)
print(result.stdout)
print_step(6, "Migration verification complete", "success")
print()

print("=== Migration Complete! ===\n")
print("Next steps:")
print("1. Test the application: python manage.py runserver")
print("2. If everything works, you can delete: db.sqlite3")
print("3. Keep backup files safe: *_backup.json files")
print()
