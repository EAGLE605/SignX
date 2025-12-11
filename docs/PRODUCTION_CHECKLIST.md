# SignX Production Deployment Checklist

**Generated**: 2025-12-11
**Status**: Ready for Review

---

## Pre-Deployment Verification

### 1. Security Fixes Applied

- [x] Webhook signature validation implemented (`routes/crm.py`)
- [x] HMAC-SHA256 with timing-safe comparison
- [x] Graceful fallback for development mode
- [x] Hardcoded database URLs replaced with `settings.DATABASE_URL`
  - `routes/poles_aisc.py`
  - `routes/monument.py`
  - `scripts/generate_test_data.py`

### 2. Configuration Files Created

- [x] `infra/.env.example` - Complete production environment template
- [x] `docs/PRODUCTION_READINESS_GUIDE.md` - 7-step deployment guide
- [x] `docs/PRODUCTION_AUDIT_REPORT.md` - Vulnerability findings

### 3. Dependency Updates Required

**Before deploying to production, run:**

```bash
pip install --upgrade \
    cryptography>=43.0.1 \
    setuptools>=78.1.1 \
    urllib3>=2.6.0 \
    pip>=25.3
```

| Package | Current | Required | CVE |
|---------|---------|----------|-----|
| cryptography | 41.0.7 | 43.0.1+ | CVE-2023-50782, CVE-2024-0727 |
| setuptools | 68.1.2 | 78.1.1+ | CVE-2024-6345 |
| urllib3 | 2.5.0 | 2.6.0+ | CVE-2025-66418 |
| pip | 24.0 | 25.3+ | CVE-2025-8869 |

---

## Deployment Steps

### Step 1: Environment Setup

```bash
# Copy example config
cp infra/.env.example infra/.env

# Edit with production values
nano infra/.env
```

**Required Variables:**
- `POSTGRES_PASSWORD` - Strong password for database
- `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` - Object storage credentials
- `SUPABASE_URL` / `SUPABASE_KEY` - Authentication service
- `JWT_SECRET_KEY` - 256-bit secret for token signing
- `CORS_ALLOW_ORIGINS` - Production domain(s)

### Step 2: Build & Deploy

```bash
# Build production images
docker build -t signx-api:prod services/api/
docker build -t signx-worker:prod services/worker/

# Deploy with production config
docker-compose -f infra/compose.yaml up -d

# Verify health
curl -f http://localhost:8000/health
curl -f http://localhost:8000/ready
```

### Step 3: Run Migrations

```bash
cd services/api
alembic upgrade head
```

### Step 4: Smoke Test

```bash
# Run smoke test
python scripts/smoke.py

# Or via make
make smoke
```

---

## Post-Deployment Monitoring

### Health Endpoints

| Endpoint | Purpose | Expected |
|----------|---------|----------|
| `/health` | Liveness | `{"ok": true}` |
| `/ready` | Readiness | All services green |
| `/docs` | API Docs | Swagger UI |

### Metrics & Dashboards

- **Grafana**: http://localhost:3001
- **MinIO Console**: http://localhost:9001
- **OpenSearch**: http://localhost:5601

### First 24 Hours

- [ ] Monitor error rates in Sentry
- [ ] Check API latency (target: <500ms p95)
- [ ] Verify quote generation flow
- [ ] Test webhook integrations
- [ ] Review authentication logs

---

## Remaining TODOs (Non-Blocking)

These items are documented but not blocking production:

| Priority | Item | Location |
|----------|------|----------|
| Medium | PM system API integration | `worker/tasks.py:103` |
| Medium | Email service integration | `worker/tasks.py:152` |
| Medium | NOAA ASOS wind data lookup | `utils/wind_data.py:84` |
| Low | Gemini response parsing | `modules/rag/__init__.py` |
| Low | CostPredictor import | `modules/intelligence/__init__.py` |

---

## Rollback Procedure

```bash
# Tag current version before deploy
docker tag signx-api:prod signx-api:rollback-$(date +%Y%m%d)

# If issues detected
docker-compose down
docker tag signx-api:rollback-YYYYMMDD signx-api:prod
docker-compose up -d

# Rollback database if needed
cd services/api
alembic downgrade -1
```

---

## Sign-Off

| Role | Name | Date | Approved |
|------|------|------|----------|
| Developer | Claude Code | 2025-12-11 | [x] |
| Security | _______________ | ________ | [ ] |
| DevOps | _______________ | ________ | [ ] |
| Product | _______________ | ________ | [ ] |

---

**Ready for production deployment pending security and DevOps review.**
