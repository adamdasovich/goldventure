# GoldVenture Platform - Setup Guide

## 🎯 What We Just Built

Your Django project structure is now complete with:

✅ Full Django project configuration
✅ 20 database models for mining IR platform
✅ Django admin interface
✅ MCP server folder structure
✅ Claude integration folder structure
✅ All configuration files

---

## 📋 Next Steps - Do These NOW

### Step 1: Set Up PostgreSQL Database

You need PostgreSQL installed on your system.

**Check if PostgreSQL is installed:**
```bash
psql --version
```

**If not installed:**
- **Windows**: Download from https://www.postgresql.org/download/windows/
- **Mac**: `brew install postgresql@15`
- **Linux**: `sudo apt-get install postgresql postgresql-contrib`

**Create the database:**
```bash
# Start PostgreSQL service (if not running)
# Windows: Check Services app
# Mac: brew services start postgresql
# Linux: sudo service postgresql start

# Create database
createdb goldventure_db

# Or using psql:
psql -U postgres
CREATE DATABASE goldventure_db;
\q
```

---

### Step 2: Create Virtual Environment & Install Dependencies

```bash
cd C:\Users\adamd\Desktop\Nvidia\goldventure-platform\backend

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

---

### Step 3: Configure Environment Variables

```bash
# Copy the example file
copy .env.example .env

# Edit .env with your actual values:
```

**Edit `.env` file** with these minimum settings:

```bash
DEBUG=True
SECRET_KEY=change-this-to-something-random-and-secret

# Database
DB_NAME=goldventure_db
DB_USER=postgres
DB_PASSWORD=your-postgres-password-here
DB_HOST=localhost
DB_PORT=5432

# Claude API (get from https://console.anthropic.com/)
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Alpha Vantage (get free key from https://www.alphavantage.co/support/#api-key)
ALPHA_VANTAGE_API_KEY=your-key-here

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

---

### Step 4: Run Database Migrations

```bash
# Make sure you're in backend/ folder with venv activated
cd C:\Users\adamd\Desktop\Nvidia\goldventure-platform\backend

# Create migration files
python manage.py makemigrations

# Apply migrations to database
python manage.py migrate
```

You should see output like:
```
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying core.0001_initial... OK
  ...
  Applying core.0002_auto_20250115... OK
```

---

### Step 5: Create Your Admin User

```bash
python manage.py createsuperuser

# Enter your details:
# Username: adam
# Email: adamdasovich@gmail.com
# Password: (choose a strong password)
```

---

### Step 6: Start the Development Server

```bash
python manage.py runserver
```

You should see:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

### Step 7: Test the Admin Interface

1. **Open browser**: http://localhost:8000/admin/
2. **Login** with your superuser credentials
3. **You should see** all your models:
   - Companies
   - Projects
   - Resource Estimates
   - Economic Studies
   - Financings
   - Investors
   - etc.

---

## 🎉 Success Criteria

If you can do all of these, you're ready to move on:

- [ ] PostgreSQL is running
- [ ] Virtual environment is activated
- [ ] All dependencies installed (no errors)
- [ ] `.env` file configured with API keys
- [ ] Migrations ran successfully
- [ ] Superuser created
- [ ] Development server is running
- [ ] Can login to Django admin at http://localhost:8000/admin/
- [ ] Can see all 20+ models in admin interface

---

## 🐛 Troubleshooting

### Problem: "pg_config executable not found"

**Solution**: Install PostgreSQL development files
```bash
# Windows: Make sure PostgreSQL bin folder is in PATH
# Mac: brew install postgresql
# Linux: sudo apt-get install libpq-dev
```

### Problem: "password authentication failed for user postgres"

**Solution**: Reset PostgreSQL password
```bash
psql -U postgres
ALTER USER postgres PASSWORD 'your-new-password';
\q
```

Then update your `.env` file with the new password.

### Problem: "ModuleNotFoundError: No module named 'anthropic'"

**Solution**: Make sure virtual environment is activated
```bash
# You should see (venv) at the start of your command prompt
venv\Scripts\activate

# Then reinstall
pip install -r requirements.txt
```

### Problem: "ANTHROPIC_API_KEY not set"

**Solution**: Get your API key from https://console.anthropic.com/
1. Create account / Login
2. Go to API Keys
3. Create new key
4. Copy to `.env` file

---

## ✅ Once Setup is Complete

**You're ready for the next step:**

1. **Add sample data** through Django admin
   - Create your first Company
   - Add a Project
   - Add a Resource Estimate
   - Add a Financing

2. **Then we'll build**:
   - Mining Data MCP Server
   - Claude integration client
   - Test queries like "What are our total resources?"

---

## 📞 If You Get Stuck

**Check these first:**
1. Is PostgreSQL running? (Check Services on Windows)
2. Is virtual environment activated? (See `(venv)` in prompt)
3. Are all packages installed? (`pip list` should show Django, anthropic, etc.)
4. Did migrations run? (`python manage.py showmigrations` - should show [X] for all)

**Still stuck?**
- Take a screenshot of the error
- Note what command you ran
- We'll troubleshoot together!

---

## 🚀 You're On Your Way!

Once you complete this setup, you'll have:
- ✅ A production-grade database schema
- ✅ Full Django backend running
- ✅ Admin interface for data entry
- ✅ Ready for MCP server implementation

**This is solid foundation.** Next we build the AI layer! 💪

---

**Current Status**: Week 1, Day 1 - Foundation Complete!

**Next Session**: Build the Mining Data MCP Server with 5 core tools
