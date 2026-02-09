# GoldVenture Platform

AI-powered Investor Relations & Intelligence Platform for Junior Gold Mining Companies

Built by Adam Dasovich | [GitHub](https://github.com/adamdasovich)

---

## Overview

GoldVenture is a Django + Next.js platform that uses **Claude AI with MCP (Model Context Protocol)** to provide natural language access to mining company data, investor relations tracking, and market intelligence.

### Key Features

- **Claude-Powered Q&A**: Ask questions about projects, resources, financings in plain English
- **Mining Data Management**: Track projects, NI 43-101 resources, economic studies
- **Investor CRM**: Manage investor relationships, communications, and positions
- **Market Intelligence**: Real-time commodity prices, stock data, peer comparisons
- **Document Intelligence**: AI-powered extraction from technical reports (PDF)

---

## Technology Stack

**Backend:**
- Django 5.0 + Django REST Framework
- PostgreSQL database
- Claude API with custom MCP servers
- Python 3.11+

**Frontend:**
- Next.js 14 (React)
- TypeScript
- Tailwind CSS

**AI/ML:**
- Anthropic Claude Sonnet 4.5
- Custom MCP servers for mining data
- PDF extraction (PyPDF2, pdfplumber)

**External APIs:**
- Alpha Vantage (market data)
- AWS S3 (document storage)

---

## Project Structure

```
goldventure-platform/
├── backend/
│   ├── config/                 # Django settings
│   ├── core/                   # Main app (models, views, admin)
│   ├── mcp_servers/            # MCP server implementations
│   │   ├── base.py            # Base MCP server class
│   │   ├── mining_data.py     # Mining Data MCP Server
│   │   ├── financial_data.py  # Financial Data MCP Server
│   │   └── investor_relations.py  # IR MCP Server
│   ├── claude_integration/     # Claude API wrapper
│   │   ├── client.py          # ClaudeClient class
│   │   └── tools.py           # Tool management
│   ├── manage.py
│   └── requirements.txt
├── frontend/                   # Next.js app (coming soon)
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Node.js 18+ (for frontend)
- Anthropic API key
- Alpha Vantage API key (free tier OK)

### 1. Clone & Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings:
# - DATABASE credentials
# - ANTHROPIC_API_KEY
# - ALPHA_VANTAGE_API_KEY
```

### 3. Set Up Database

```bash
# Create PostgreSQL database
createdb goldventure_db

# Or using psql:
psql -U postgres
CREATE DATABASE goldventure_db;
\q

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 4. Run Development Server

```bash
python manage.py runserver
```

Visit:
- **Admin**: http://localhost:8000/admin/
- **API**: http://localhost:8000/api/

---

## Database Schema

The platform tracks 20+ entities across 5 main categories:

### Companies & Projects
- `companies` - Junior mining companies
- `projects` - Mining projects (multiple per company)
- `resource_estimates` - NI 43-101 resources
- `economic_studies` - PEA/PFS/FS results

### Financing & Investors
- `financings` - Capital raises
- `investors` - Individual & institutional
- `investor_positions` - Shareholdings
- `investor_communications` - CRM tracking

### Market & Analytics
- `market_data` - Daily price/volume
- `commodity_prices` - Gold/silver prices
- `company_metrics` - Quarterly snapshots
- `news_releases` - Press releases

### Other
- `users` - Platform users
- `documents` - File library
- `watchlists` - User-created lists
- `alerts` - Price/news alerts

See [core/models.py](backend/core/models.py) for complete schema.

---

## Development Roadmap

### ✅ Phase 0: Foundation (Current)
- [x] Django project structure
- [x] Database models & migrations
- [ ] PostgreSQL setup
- [ ] Admin interface configured

### 🔨 Phase 1: MCP Servers (Week 1-2)
- [ ] Mining Data MCP Server (5 core tools)
- [ ] Financial Data MCP Server
- [ ] Claude integration client
- [ ] Basic API endpoints

### 🔨 Phase 2: Frontend (Week 3-4)
- [ ] Next.js project setup
- [ ] Claude chat interface
- [ ] Company/project data entry forms
- [ ] Authentication (JWT)

### 🔨 Phase 3: Features (Week 5-6)
- [ ] Investor CRM
- [ ] Dashboard with charts
- [ ] Document upload
- [ ] PDF auto-extraction

### 🚀 Phase 4: Production (Week 7+)
- [ ] AWS deployment (RDS, S3, EC2)
- [ ] Alpha Vantage integration
- [ ] Performance optimization
- [ ] First client onboarding

---

## MCP Server Architecture

GoldVenture uses **3 custom MCP servers** to provide Claude with domain-specific capabilities:

### 1. Mining Data Server
Tools for querying projects, resources, and technical data:
- `mining_get_total_resources` - Aggregate resources across projects
- `mining_get_project_details` - Detailed project information
- `mining_list_projects` - List/filter projects
- `mining_get_latest_economic_study` - PEA/PFS/FS data
- `mining_compare_resource_estimates` - Historical resource growth

### 2. Financial Data Server
Tools for financings, valuations, and market data:
- `financial_get_financing_history` - Capital raises timeline
- `financial_get_total_raised` - Total capital by period
- `financial_get_cash_position` - Current cash & burn rate
- `financial_get_market_data` - Stock price/volume charts

### 3. Investor Relations Server (Phase 2)
Tools for investor management:
- `investor_search` - Find investors by criteria
- `investor_get_profile` - Full investor details
- `investor_log_communication` - Track meetings/calls
- `investor_create_list` - Generate targeted lists

---

## Example Usage

### Claude Chat Examples

**Query 1: Resource Aggregation**
```
User: "What are our total measured & indicated gold resources?"

Claude: [calls mining_get_total_resources]
"You have 1.2 million ounces of measured & indicated gold resources
across 3 projects:
- Gold Ridge: 400K oz @ 2.5 g/t
- Silver Peak: 600K oz @ 1.8 g/t
- Valley Project: 200K oz @ 3.2 g/t"
```

**Query 2: Financing History**
```
User: "How much have we raised in the last 2 years?"

Claude: [calls financial_get_total_raised]
"In the past 2 years, you've raised $8.2M across 3 financings:
- Oct 2023: $3.5M private placement @ $0.25/share
- Mar 2024: $2.8M flow-through @ $0.35/share
- Jun 2024: $1.9M warrant exercise"
```

---

## Environment Variables

```bash
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=goldventure_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# APIs
ANTHROPIC_API_KEY=sk-ant-api03-...
ALPHA_VANTAGE_API_KEY=your-key

# AWS (for production)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=goldventure-documents
AWS_S3_REGION_NAME=us-east-1

# CORS (for Next.js)
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

---

## Testing

```bash
# Run Django tests
python manage.py test

# Run specific app tests
python manage.py test core

# Test MCP servers directly
python test_mcp_servers.py
```

---

## Deployment

### Development
- Django: `python manage.py runserver`
- Next.js: `npm run dev`

### Production (AWS)
- **Database**: RDS PostgreSQL
- **Backend**: EC2 or ECS
- **Frontend**: Vercel or Amplify
- **Storage**: S3 for documents

Deployment guide coming in Phase 4.

---

## API Documentation

### Authentication

```bash
# Get JWT token
POST /api/token/
{
  "username": "your-username",
  "password": "your-password"
}

# Response
{
  "access": "<YOUR_ACCESS_TOKEN>",
  "refresh": "<YOUR_REFRESH_TOKEN>"
}

# Use token in requests
Authorization: Bearer <YOUR_ACCESS_TOKEN>
```

### Claude Chat

```bash
POST /api/claude/chat/
{
  "message": "What are our total resources?",
  "conversation_history": []  # optional
}

# Response
{
  "message": "You have 1.2M oz M&I gold across 3 projects...",
  "tool_calls": [
    {
      "tool": "mining_get_total_resources",
      "input": {"category": "mni"},
      "result": {...}
    }
  ],
  "usage": {
    "input_tokens": 1234,
    "output_tokens": 567
  }
}
```

---

## Contributing

This is currently a solo project by Adam Dasovich.

If you're interested in contributing or using this for your junior mining company, reach out:
- **Email**: adamdasovich@gmail.com
- **LinkedIn**: [Link to your LinkedIn]
- **GitHub**: [@adamdasovich](https://github.com/adamdasovich)

---

## License

Proprietary - All Rights Reserved

This software is being developed for commercial use. Contact for licensing inquiries.

---

## Credits

**Built by**: Adam Dasovich
**Tech Stack**: Django, Next.js, PostgreSQL, Claude AI (Anthropic)
**Domain Expertise**: 25+ years in mining engineering, finance, and capital markets
- BSc Materials & Metallurgical Engineering (Queen's University)
- CFA Charterholder
- Former CEO, Mining Analyst, Plant Manager

---

## Changelog

### v0.1.0 - 2025-01-15
- Initial project structure
- Database models (20 tables)
- Django admin interface
- MCP server architecture designed

---

## Next Steps

1. **Immediate**: Set up PostgreSQL database and run migrations
2. **This Week**: Build Mining Data MCP Server
3. **Week 2**: Implement Claude integration
4. **Week 3-4**: Build Next.js frontend
5. **Week 5-6**: Add investor CRM and PDF extraction
6. **Week 7+**: Deploy to AWS, onboard first client

---

**Status**: 🚧 In Development (Week 1 of 6-week MVP sprint)

Last Updated: 2025-01-15
