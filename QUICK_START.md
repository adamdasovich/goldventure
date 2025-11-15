# Quick Start Commands

## Initial Setup (Do Once)

```bash
# 1. Navigate to project
cd C:\Users\adamd\Desktop\Nvidia\goldventure-platform\backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file
copy .env.example .env
# THEN EDIT .env with your API keys and database password

# 6. Create PostgreSQL database
createdb goldventure_db

# 7. Run migrations
python manage.py makemigrations
python manage.py migrate

# 8. Create superuser
python manage.py createsuperuser

# 9. Run server
python manage.py runserver
```

---

## Daily Development (Every Time)

```bash
# 1. Navigate to backend
cd C:\Users\adamd\Desktop\Nvidia\goldventure-platform\backend

# 2. Activate virtual environment
venv\Scripts\activate

# 3. Run server
python manage.py runserver
```

**Open**: http://localhost:8000/admin/

---

## Useful Commands

### Database

```bash
# Make new migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations

# Open Django shell (Python REPL with models loaded)
python manage.py shell
```

### Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test core

# Run with verbose output
python manage.py test --verbosity=2
```

### Database Inspection

```bash
# Django shell examples
python manage.py shell

>>> from core.models import Company, Project
>>> Company.objects.all()
>>> Company.objects.create(name="Test Mining Co", status="private")
>>> Project.objects.filter(company__name__contains="Test")
```

### Admin Management

```bash
# Create another superuser
python manage.py createsuperuser

# Change password
python manage.py changepassword username
```

---

## Project Structure Reference

```
backend/
├── config/              # Django settings, URLs
├── core/               # Main app
│   ├── models.py       # 20 database models ← YOUR DATA SCHEMA
│   ├── views.py        # API endpoints
│   ├── admin.py        # Admin interface
│   └── urls.py         # URL routing
├── mcp_servers/        # MCP server implementations (NEXT)
├── claude_integration/ # Claude API client (NEXT)
└── manage.py          # Django management script
```

---

## API Endpoints (Coming Soon)

```bash
# Authentication
POST /api/token/                    # Get JWT token
POST /api/token/refresh/            # Refresh token

# Claude Integration (to be built)
POST /api/claude/chat/              # Chat with Claude
GET  /api/claude/tools/             # List available MCP tools
```

---

## Environment Variables (.env)

```bash
# Django
DEBUG=True
SECRET_KEY=your-secret-key

# Database
DB_NAME=goldventure_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# APIs
ANTHROPIC_API_KEY=sk-ant-api03-...
ALPHA_VANTAGE_API_KEY=your-key
```

---

## Git Commands (When Ready)

```bash
# Initialize git (if not done)
cd C:\Users\adamd\Desktop\Nvidia\goldventure-platform
git init

# First commit
git add .
git commit -m "Initial Django project structure with models"

# Daily commits
git add .
git commit -m "Implemented Mining Data MCP Server"
git push
```

---

## Port Reference

- **Django**: http://localhost:8000
- **Next.js** (later): http://localhost:3000
- **PostgreSQL**: localhost:5432

---

## File Locations

- **Models**: `backend/core/models.py`
- **Settings**: `backend/config/settings.py`
- **Environment**: `backend/.env`
- **Requirements**: `backend/requirements.txt`
- **Admin**: `backend/core/admin.py`

---

## Next Implementation Steps

### Week 1 (This Week)
- [ ] Complete setup (SETUP_GUIDE.md)
- [ ] Add sample company data via admin
- [ ] Build Mining Data MCP Server
- [ ] Build Claude integration client
- [ ] Test first query: "What are our total resources?"

### Week 2
- [ ] Build Financial Data MCP Server
- [ ] Expand MCP tools
- [ ] Build API endpoints for CRUD operations
- [ ] Test end-to-end flow

### Week 3-4
- [ ] Set up Next.js frontend
- [ ] Build Claude chat UI
- [ ] Data entry forms
- [ ] Authentication flow

---

## Tips

1. **Always activate venv** before working
2. **Check migrations** after changing models
3. **Use Django admin** to add test data
4. **Test in shell** before writing views
5. **Commit often** to git

---

## Quick Reference URLs

- **Anthropic Console**: https://console.anthropic.com/
- **Alpha Vantage**: https://www.alphavantage.co/
- **Django Docs**: https://docs.djangoproject.com/
- **DRF Docs**: https://www.django-rest-framework.org/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/

---

**You've got this! 🚀**

Next: Follow SETUP_GUIDE.md to get everything running!
