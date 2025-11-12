# Daily Drill Report System (DRS)

[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

A comprehensive Django-based web application for managing and tracking drilling operations, progress reporting, and bill of quantities (BOQ) generation. Built for Leos Investments Ltd to streamline drilling data collection, approval workflows, and analytics.

![Project Logo](core/static/core/images/logo.png)

## ✨ Features

### Core Functionality
- **Role-Based Access Control**
  - 👷 **Supervisor**: Create and manage drill shifts, record progress
  - 👨‍💼 **Manager**: Review, approve/reject submissions, oversight
  - 🏢 **Client**: View approved reports, access BOQ, client dashboard

- **Shift Management**
  - 📅 Day/Night shift tracking (24-hour combined view)
  - 📊 Real-time drilling progress monitoring
  - 📸 Core tray image uploads with thumbnail preview
  - ⏱️ Activity logging with duration tracking
  - 📦 Material consumption recording
  - 🔄 Multi-step approval workflow (Manager → Client)

- **Reporting & Analytics**
  - 📈 Interactive activity breakdown charts (Chart.js)
  - 📋 Daily and Monthly Bill of Quantities (BOQ)
  - 📄 PDF export (receipt-style reports)
  - 📊 Excel/CSV export (multi-format support)
  - 🔍 Advanced filtering (date, rig, hole number, status)
  - 📉 Drilling efficiency metrics (penetration rate, recovery %)

### Data Management
- ✅ Automatic calculations (meters drilled, man-hours, activity hours)
- ✅ Data validation and integrity checks
- ✅ Audit trail and approval history
- ✅ Backup and restore capabilities
- ✅ Image optimization and storage

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/MansLikeNight/DRS-.git
cd DRS-
```

2. **Create and activate a virtual environment:**
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
# Copy the example file
cp .env.example .env

# Edit .env and set your SECRET_KEY and other settings
# For development, the defaults work fine
```

5. **Apply database migrations:**
```bash
python manage.py migrate
```

6. **Create a superuser:**
```bash
python manage.py createsuperuser
```

7. **Collect static files:**
```bash
python manage.py collectstatic --noinput
```

8. **Run the development server:**
```bash
python manage.py runserver
```

9. **Access the application:**
   - Open your browser and navigate to `http://localhost:8000`
   - Admin panel: `http://localhost:8000/admin`

## 📦 Technology Stack

### Backend
- **Django 5.0** - Web framework with ORM
- **Python 3.11+** - Programming language
- **SQLite** (Development) / **PostgreSQL** (Production)

### Frontend
- **Bootstrap 5** - UI framework
- **Chart.js 4.4** - Interactive charts
- **Vanilla JavaScript** - Client-side logic

### File Processing
- **Pillow 12.0.0** - Image processing
- **ReportLab 4.4.4** - PDF generation
- **xlsxwriter 3.2.9** - Excel export

### Production
- **Gunicorn 23.0.0** - WSGI server
- **WhiteNoise 6.9.0** - Static file serving
- **psycopg2-binary 2.9.11** - PostgreSQL adapter

## 📁 Project Structure

```
DailyDrillReport/
├── 📂 accounts/              # User authentication and profiles
│   ├── models.py            # UserProfile model
│   ├── views.py             # Login, register, profile views
│   ├── forms.py             # Authentication forms
│   ├── middleware.py        # Profile creation middleware
│   └── templates/           # Auth-related templates
├── 📂 core/                  # Main application logic
│   ├── models.py            # DrillShift, DrillingProgress, etc.
│   ├── views.py             # Shift CRUD, approval, exports
│   ├── forms.py             # Formsets and validation
│   ├── utils.py             # BOQ and export utilities
│   ├── pdf_utils.py         # PDF generation logic
│   ├── static/              # CSS, JS, images
│   ├── templates/           # HTML templates
│   └── tests/               # Unit tests
├── 📂 DailyDrillReport/      # Project settings
│   ├── settings.py          # Django configuration
│   ├── urls.py              # URL routing
│   └── wsgi.py              # WSGI entry point
├── 📂 media/                 # Uploaded files (core tray images)
├── 📂 staticfiles/           # Collected static files (production)
├── 📄 .env.example           # Environment variables template
├── 📄 .gitignore             # Git ignore rules
├── 📄 requirements.txt       # Python dependencies
├── 📄 Procfile               # Production deployment config
├── 📄 runtime.txt            # Python version specification
├── 📄 README.md              # This file
├── 📄 DATA_ENGINEERING.md    # Data pipeline documentation
├── 📄 PRODUCTION_DEPLOYMENT.md  # Deployment guide
└── 📄 PRODUCTION_CHECKLIST.md   # Pre-deployment checklist
```

## 🎯 Usage

### User Workflows

#### 1. Supervisor Workflow
1. **Login** to the system
2. **Create New Shift** with basic info (date, rig, crew)
3. **Add Drilling Progress**:
   - Hole number, depth range (from/to)
   - Size (HQ/NQ/PQ/BQ)
   - Start/end times
   - Core recovery percentage
   - Upload core tray images (optional)
4. **Log Activities**: drilling, maintenance, safety, meetings
5. **Record Materials**: name, quantity, unit
6. **Submit for Approval** → Manager review

#### 2. Manager Workflow
1. **Review Submitted Shifts** on dashboard
2. **View Shift Details** with all data
3. **Approve or Reject** with optional comments
4. **Track Approval History**
5. **Generate BOQ Reports** (daily/monthly)
6. **Export Data** (PDF, Excel, CSV)

#### 3. Client Workflow
1. **Access Client Dashboard** (dedicated portal)
2. **Review Shifts** submitted for client approval
3. **Approve or Reject** with feedback
4. **View Approved Shifts** and historical data
5. **Download BOQ Reports** and exports
6. **Track 24-Hour Metrics** (combined day/night)

### Key Features Demonstration

**24-Hour Combined View:**
- Automatically pairs day and night shifts
- Shows combined totals (meters, man-hours, activities)
- Side-by-side comparison cards
- Collapsible detailed sections

**Activity Breakdown Chart:**
- Visual representation of shift activities
- Drilling, maintenance, safety, standby hours
- Interactive Chart.js visualization
- Automatic calculations from time logs

**BOQ Generation:**
- Filter by date range, client, hole number
- Aggregate drilling progress by hole
- Calculate totals and averages
- Export to Excel with formatting

**Approval Workflow:**
```
Draft → Submitted → Manager Approved → Client Approved → Locked
  ↓          ↓              ↓                ↓
Edit    Wait Review     Wait Client     Final State
        ← Rejected ←    ← Rejected ←
           (Re-edit)       (Re-edit)
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test core
python manage.py test accounts

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

### Test Coverage
- ✅ Model validation tests
- ✅ View logic tests
- ✅ Form validation tests
- ✅ Utility function tests
- ✅ Workflow integration tests

## 🚀 Production Deployment

### Environment Configuration

1. **Set production environment variables** in `.env`:
```bash
DEBUG=False
SECRET_KEY=your-production-secret-key-here
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432
```

2. **Collect static files:**
```bash
python manage.py collectstatic --noinput
```

3. **Run migrations:**
```bash
python manage.py migrate
```

4. **Create superuser:**
```bash
python manage.py createsuperuser
```

### Deployment Platforms

#### Render (Recommended)
See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) for detailed instructions.

**Quick Steps:**
1. Push code to GitHub
2. Create PostgreSQL database on Render
3. Create Web Service, connect to repo
4. Set environment variables
5. Deploy automatically

#### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

#### Heroku
```bash
# Install Heroku CLI and deploy
heroku create your-app-name
heroku addons:create heroku-postgresql:mini
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

### Production Checklist
See [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md) for complete list.

**Critical items:**
- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up PostgreSQL database
- [ ] Configure email backend (password resets)
- [ ] Enable HTTPS/SSL
- [ ] Set up automated backups
- [ ] Configure CDN for static files (optional)
- [ ] Set up monitoring and logging

## 📊 Data Engineering

For comprehensive documentation on the data pipeline, ETL processes, analytics capabilities, and upgrade roadmap, see [DATA_ENGINEERING.md](DATA_ENGINEERING.md).

**Highlights:**
- 5-layer data pipeline architecture
- Automated ETL processes
- Real-time analytics with Chart.js
- BOQ generation and aggregation
- Multiple export formats (PDF, Excel, CSV)
- Future enhancements: ML models, streaming pipelines, data warehouse

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes and commit**:
   ```bash
   git add .
   git commit -m "Add: Description of your feature"
   ```
4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Create a Pull Request** on GitHub

### Commit Message Convention
```
Add: New feature
Fix: Bug fix
Update: Improve existing feature
Refactor: Code restructuring
Docs: Documentation updates
Test: Add or update tests
```

### Code Standards
- Follow PEP 8 style guide
- Write docstrings for functions and classes
- Add unit tests for new features
- Update documentation as needed

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors & Contributors

- **Night** - *Initial work* - [MansLikeNight](https://github.com/MansLikeNight)

See also the list of [contributors](https://github.com/MansLikeNight/DRS-/contributors) who participated in this project.

## 🙏 Acknowledgments

- Built for **Leos Investments Ltd**
- Django framework and community
- Bootstrap team for UI components
- Chart.js for interactive visualizations
- ReportLab for PDF generation
- All open-source contributors

## 📧 Support

For questions, issues, or feature requests:

- **GitHub Issues**: [Create an issue](https://github.com/MansLikeNight/DRS-/issues)
- **Email**: support@leosinvestments.com (if applicable)
- **Documentation**: See `PRODUCTION_DEPLOYMENT.md` and `DATA_ENGINEERING.md`

## 📸 Screenshots

### Dashboard
![Dashboard](docs/screenshots/dashboard.png)

### Shift Detail (24-Hour View)
![Shift Detail](docs/screenshots/shift-detail.png)

### Activity Breakdown Chart
![Activity Chart](docs/screenshots/activity-chart.png)

### BOQ Report
![BOQ Report](docs/screenshots/boq-report.png)

---

## 🗺️ Roadmap

### Version 1.0 (Current)
- ✅ Core shift management
- ✅ Approval workflow
- ✅ BOQ generation
- ✅ PDF/Excel/CSV exports
- ✅ 24-hour combined view
- ✅ Activity charts

### Version 1.1 (Planned)
- [ ] REST API with Django REST Framework
- [ ] Mobile-responsive PWA
- [ ] Real-time notifications
- [ ] Advanced filtering and search
- [ ] Dashboard KPIs and metrics

### Version 2.0 (Future)
- [ ] Predictive analytics (ML models)
- [ ] Real-time data streaming
- [ ] Interactive dashboards (Plotly Dash)
- [ ] Mobile app (React Native)
- [ ] Multi-tenant SaaS platform

See [DATA_ENGINEERING.md](DATA_ENGINEERING.md) for detailed upgrade roadmap.

---

**Built with ❤️ for efficient drilling operations management**