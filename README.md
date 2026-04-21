# 🛡️ Rubiscape Alert Service

**Enterprise AI Workflow Notification & Alerting Service**

A production-ready backend system that monitors AI workflow execution events, evaluates rule-based conditions, generates severity-based alerts, dispatches email notifications, and provides reporting with a web dashboard.

---

## 🏗 System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                              │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ Swagger /docs│  │  Dashboard   │  │  External Clients  │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬───────────┘  │
└─────────┼─────────────────┼───────────────────┼──────────────┘
          │                 │                   │
          ▼                 ▼                   ▼
┌──────────────────────────────────────────────────────────────┐
│                    API LAYER (FastAPI Routes)                │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ /rules/  │ │ /events/  │ │ /alerts/ │ │ /dashboard   │   │
│  │   CRUD   │ │  Ingest   │ │  Query   │ │  Jinja2 UI   │   │
│  └────┬─────┘ └─────┬─────┘ └────┬─────┘ └──────┬───────┘   │
└───────┼─────────────┼────────────┼───────────────┼───────────┘
        │             │            │               │
        ▼             ▼            ▼               ▼
┌──────────────────────────────────────────────────────────────┐
│                 SERVICE LAYER (Business Logic)               │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │              Rule Engine (rule_engine.py)            │     │
│  │  • Fetches matching rules for event metric          │     │
│  │  • Evaluates: >, <, >=, <=, == operators            │     │
│  │  • Returns list of triggered rules                  │     │
│  └──────────────────────┬──────────────────────────────┘     │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐     │
│  │           Alert Service (alert_service.py)          │     │
│  │  • Creates alert records in database                │     │
│  │  • Generates human-readable alert messages          │     │
│  │  • Triggers notification pipeline                   │     │
│  └──────────────────────┬──────────────────────────────┘     │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐     │
│  │     Notification Service (notification_service.py)  │     │
│  │  • Console logging (structured format)              │     │
│  │  • Gmail SMTP email (HTML formatted, async thread)  │     │
│  │  • Retry logic (3 attempts with backoff)            │     │
│  └─────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────┐
│                  DATA LAYER (SQLAlchemy ORM)                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │  Rules   │  │  Events  │  │  Alerts  │                   │
│  │  Table   │  │  Table   │  │  Table   │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
│                     SQLite / MySQL                           │
└──────────────────────────────────────────────────────────────┘
```

## 🔄 System Flow

```
AI Workflow Event (metric + value)
        │
        ▼
  POST /events/  ──────────────▶  Store Event in DB
        │
        ▼
  Rule Engine Evaluation
  (fetch all rules for metric)
        │
        ▼
  Condition Matched?  ──── No ──▶  Return (no alerts)
        │
       Yes
        │
        ▼
  Generate Alert(s)  ──────────▶  Store Alert in DB
        │
        ▼
  Notification Pipeline
  ├── Console Log (immediate)
  └── Email to Admin (async)
        │
        ▼
  Dashboard & Metrics Updated
```

## 📊 System Metrics Monitored

| Metric | Description | Example Rule |
|--------|-------------|-------------|
| **latency** | Response time in ms | `latency > 200` → HIGH |
| **error_rate** | Error percentage | `error_rate > 5` → HIGH |
| **cpu_usage** | CPU utilization % | `cpu_usage >= 95` → CRITICAL |
| **gpu_usage** | GPU utilization % | `gpu_usage >= 85` → HIGH |
| **memory_usage** | Memory utilization % | `memory_usage >= 85` → HIGH |
| **throughput** | Requests per second | `throughput < 50` → HIGH |
| **disk_usage** | Disk utilization % | `disk_usage >= 85` → HIGH |

## 📁 Project Structure

```
rubiscape_alert_service/
├── app/
│   ├── main.py              # FastAPI entry point, router registration
│   ├── database.py          # SQLAlchemy engine, session, get_db()
│   ├── core/
│   │   └── config.py        # Environment-based configuration
│   ├── models/
│   │   ├── rule.py          # Rule ORM model
│   │   ├── event.py         # Event ORM model
│   │   └── alert.py         # Alert ORM model
│   ├── schemas/
│   │   ├── rule_schema.py   # Pydantic validation (RuleCreate/Update/Response)
│   │   └── event_schema.py  # Pydantic validation (EventCreate/Response)
│   ├── routes/
│   │   ├── rule_routes.py   # CRUD: POST/GET/PUT/DELETE /rules/
│   │   ├── event_routes.py  # POST /events/ (ingest + evaluate)
│   │   ├── alert_routes.py  # GET /alerts/, GET /alerts/metrics/report
│   │   └── dashboard_routes.py  # GET /dashboard (Jinja2 UI)
│   └── services/
│       ├── rule_engine.py         # Core rule evaluation logic
│       ├── alert_service.py       # Alert generation + notification trigger
│       └── notification_service.py # Email (Gmail SMTP) + console logging
├── templates/
│   └── dashboard.html       # Jinja2 dashboard template
├── static/
│   └── style.css            # Dark-themed CSS
├── demo.py                  # End-to-end demo script
├── .env                     # Configuration (DB, SMTP, App settings)
├── requirements.txt         # Python dependencies
└── README.md
```

## 🚀 Setup Instructions

### Prerequisites
- **Python 3.10+**
- **Gmail account** with App Password (for email notifications)

### 1. Install Dependencies

```bash
cd rubiscape_alert_service
pip install -r requirements.txt
```

### 2. Configure Environment

Edit `.env` with your credentials:

```env
# Database (SQLite works out of the box)
DB_TYPE=sqlite
DB_NAME=rubiscape_alerts

# Gmail SMTP (for real email notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
NOTIFICATION_EMAIL=admin@gmail.com
```

### 3. Start the Server

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Run the Demo

```bash
python demo.py
```

### 5. Access the Application

| Resource | URL |
|---|---|
| Health Check | http://localhost:8000/ |
| Swagger Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Dashboard | http://localhost:8000/dashboard |
| Metrics Report | http://localhost:8000/alerts/metrics/report |

---

## 📡 API Endpoints

### Rules Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/rules/` | Create a new rule |
| `GET` | `/rules/` | List all rules |
| `GET` | `/rules/{id}` | Get rule by ID |
| `PUT` | `/rules/{id}` | Update a rule |
| `DELETE` | `/rules/{id}` | Delete a rule |

### Event Ingestion
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/events/` | Ingest event → auto evaluate rules → generate alerts |
| `GET` | `/events/` | List all events |

### Alerts & Metrics
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/alerts/` | List alerts (filter by severity/service) |
| `GET` | `/alerts/metrics/report` | Metrics report (totals, by severity/service, trends) |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboard` | Web dashboard with alert table, filters, stats |

---

## 🧪 Demo Script Output

```bash
$ python demo.py

═══════════════════════════════════════════════════════════════
  STEP 1: Creating Alert Rules
═══════════════════════════════════════════════════════════════
  Rule #1:  latency         >   500.0  [CRITICAL]
  Rule #2:  latency         >   200.0  [HIGH]
  Rule #3:  error_rate      >     5.0  [HIGH]
  Rule #4:  cpu_usage       >=   95.0  [CRITICAL]
  ...
  
═══════════════════════════════════════════════════════════════
  STEP 2: Simulating AI Workflow Events
═══════════════════════════════════════════════════════════════
  📡 Model Inference Service     │ latency         =   650.0 │ 3 alerts (CRITICAL, HIGH, MEDIUM)
  📡 Data Pipeline               │ error_rate      =     8.5 │ 2 alerts (HIGH, MEDIUM)
  📡 GPU Inference Engine        │ gpu_usage       =    98.0 │ 3 alerts (CRITICAL, HIGH, MEDIUM)
  ...

═══════════════════════════════════════════════════════════════
  DEMO COMPLETE
═══════════════════════════════════════════════════════════════
  ✅ Rules Created     : 21
  ✅ Events Processed  : 10
  ✅ Alerts Generated  : 25+
  ✅ Email Sent To     : desaiprasad876@gmail.com
```

---

## 🔧 Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.10+, FastAPI |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite (MySQL/PostgreSQL switchable) |
| Validation | Pydantic v2 |
| Templates | Jinja2 |
| Email | Gmail SMTP (TLS, async) |
| Server | Uvicorn |
| Config | python-dotenv |

## 🏢 Industry Alignment (Rubiscape)

| Aspect | Implementation |
|--------|---------------|
| AI Workflow Monitoring | System-level metrics from AI services |
| Enterprise Observability | Metrics reporting + dashboard |
| Governance Enforcement | Rule-based alerting with severities |
| Execution Reliability | Retry-safe notifications |
| Platform Stability | Error handling, connection pooling |

---

*Rubiscape Alert Service © 2026 — Enterprise AI Workflow Monitoring*
# Rubiscape-Alert-Service
