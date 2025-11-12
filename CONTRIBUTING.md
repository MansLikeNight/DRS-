# Contributing to Daily Drill Report System

First off, thank you for considering contributing to the Daily Drill Report System! It's people like you that make this tool better for everyone.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

**Bug Report Template:**
- **Description**: Clear description of the bug
- **Steps to Reproduce**: Numbered steps to reproduce the behavior
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Screenshots**: If applicable
- **Environment**:
  - OS: [e.g., Windows 11, macOS 14]
  - Python version: [e.g., 3.11.5]
  - Django version: [e.g., 5.0]
  - Browser: [e.g., Chrome 120]

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title** and description
- **Use case**: Why this enhancement would be useful
- **Proposed solution**: How you envision it working
- **Alternatives**: Any alternative solutions you've considered

### Pull Requests

1. **Fork the repo** and create your branch from `main`
2. **Follow the coding standards** (PEP 8 for Python)
3. **Add tests** if you've added code that should be tested
4. **Update documentation** if you've changed APIs or functionality
5. **Ensure the test suite passes** (`python manage.py test`)
6. **Write a clear commit message** following our convention

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate it: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Unix)
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Create superuser: `python manage.py createsuperuser`
7. Run tests: `python manage.py test`

## Coding Standards

### Python Style Guide (PEP 8)

- Use 4 spaces for indentation (no tabs)
- Maximum line length: 79 characters for code, 72 for comments
- Use descriptive variable names
- Add docstrings to all functions, classes, and modules

**Example:**
```python
def calculate_penetration_rate(meters_drilled, duration_hours):
    """
    Calculate drilling penetration rate.
    
    Args:
        meters_drilled (float): Total meters drilled
        duration_hours (float): Duration in hours
        
    Returns:
        float: Penetration rate in meters per hour
        
    Raises:
        ValueError: If duration_hours is zero
    """
    if duration_hours == 0:
        raise ValueError("Duration cannot be zero")
    return meters_drilled / duration_hours
```

### Django Best Practices

- Use class-based views where appropriate
- Keep views thin, models fat
- Use Django's built-in authentication
- Always use `get_object_or_404()` for single object retrieval
- Use `F()` expressions for atomic database updates
- Avoid N+1 queries (use `select_related()` and `prefetch_related()`)

### JavaScript Style

- Use ES6+ syntax
- Use `const` and `let`, avoid `var`
- Add comments for complex logic
- Keep functions small and focused

### Git Commit Messages

Follow the conventional commit format:

```
Type: Brief description (max 50 chars)

Detailed explanation if needed (max 72 chars per line)

Fixes #issue_number (if applicable)
```

**Types:**
- `Add`: New feature or functionality
- `Fix`: Bug fix
- `Update`: Improve existing feature
- `Refactor`: Code restructuring without behavior change
- `Docs`: Documentation updates
- `Test`: Add or update tests
- `Style`: Code style changes (formatting, etc.)
- `Chore`: Maintenance tasks

**Examples:**
```
Add: Core tray image upload functionality

Implement image upload for drilling progress records with
thumbnail preview and lightbox viewing.

Fixes #42
```

```
Fix: Penetration rate calculation for overnight shifts

Correct time difference calculation when shift crosses midnight.
Add validation to prevent negative durations.

Fixes #56
```

## Testing

### Running Tests

```bash
# All tests
python manage.py test

# Specific app
python manage.py test core

# Specific test case
python manage.py test core.tests.test_models.DrillShiftTestCase

# With coverage
coverage run --source='.' manage.py test
coverage report
```

### Writing Tests

- Write tests for all new features
- Test edge cases and error conditions
- Use descriptive test method names
- Group related tests in test classes

**Example:**
```python
from django.test import TestCase
from core.models import DrillShift

class DrillShiftTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.shift = DrillShift.objects.create(
            date='2025-01-01',
            rig='Rig-001',
            shift_type='day'
        )
    
    def test_meters_drilled_calculation(self):
        """Test that meters drilled is calculated correctly"""
        progress = self.shift.progress.create(
            start_depth=0,
            end_depth=50
        )
        self.assertEqual(progress.meters_drilled, 50)
    
    def test_invalid_depth_range(self):
        """Test that end depth must be greater than start depth"""
        with self.assertRaises(ValidationError):
            progress = self.shift.progress.create(
                start_depth=50,
                end_depth=30
            )
            progress.full_clean()
```

## Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Document parameters, return values, and exceptions

### User Documentation

- Update README.md for user-facing changes
- Add examples for new features
- Update PRODUCTION_DEPLOYMENT.md for deployment changes
- Update DATA_ENGINEERING.md for data model changes

## Review Process

1. **Automated checks** run on all PRs (tests, linting)
2. **Code review** by maintainer(s)
3. **Discussion** of implementation approach if needed
4. **Approval and merge** once all checks pass

## Questions?

Feel free to:
- Open an issue with the `question` label
- Contact the maintainers
- Check existing documentation

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- GitHub contributors page

Thank you for contributing! 🎉
