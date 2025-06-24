"""
# Asset Management API

## Setup Instructions

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. Create superuser (optional):
```bash
python manage.py createsuperuser
```

5. Run server:
```bash
python manage.py runserver
```

## API Endpoints

- **Swagger Documentation**: http://localhost:8000/swagger/
- **Assets CRUD**: http://localhost:8000/api/assets/
- **Notifications**: http://localhost:8000/api/notifications/
- **Violations**: http://localhost:8000/api/violations/
- **Run Checks**: http://localhost:8000/api/run-checks/

## Testing

Run tests with:
```bash
python manage.py test
```

## Usage

1. Create assets with service and expiration times
2. Use the `/api/run-checks/` endpoint to trigger periodic checks
3. View notifications and violations through their respective endpoints
4. Mark assets as serviced using `/api/assets/{id}/mark_serviced/`