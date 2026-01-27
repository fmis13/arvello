# Suggested Commands

## Development
- **Run development server**: `python manage.py runserver`
- **Create migrations**: `python manage.py makemigrations`
- **Apply migrations**: `python manage.py migrate`
- **Create superuser**: `python manage.py createsuperuser`
- **Collect static files**: `python manage.py collectstatic`

## Testing
- **Run all tests**: `python manage.py test`
- **Run specific app tests**: `python manage.py test arvelloapp`

## Environment
- **Install dependencies**: `pip install -r requirements.txt`
- **Activate virtual environment**: `source .venv/bin/activate` (or path to your venv)

## Deployment
- **Run deploy script**: `./deploy_arvello.sh` (requires root/sudo)

## Linting
- **Qodana**: Use Qodana for code analysis (configured in `qodana.yaml`)
