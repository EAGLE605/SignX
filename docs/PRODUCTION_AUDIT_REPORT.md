# SignX Production Audit Report

**Date**: 2025-12-11
**Auditor**: Claude Code
**Status**: In Progress

---

## Executive Summary

| Category | Critical | High | Medium | Low | Total |
|----------|----------|------|--------|-----|-------|
| **TODOs/Placeholders** | 0 | 8 | 19 | 5 | 32 |
| **Security Vulnerabilities** | 4 | 5 | 0 | 0 | 9 |
| **Hardcoded Credentials** | 0 | 6 | 0 | 0 | 6 |
| **Code Quality** | 0 | 0 | 2 | 0 | 2 |

---

## 1. Critical & High Priority Issues

### 1.1 Dependency Vulnerabilities (CRITICAL - 4 issues)

| Package | Version | CVE | Fix Version | Risk |
|---------|---------|-----|-------------|------|
| `cryptography` | 41.0.7 | CVE-2023-50782 | 42.0.0+ | RSA key exchange decryption |
| `cryptography` | 41.0.7 | CVE-2024-0727 | 42.0.2+ | PKCS12 NULL pointer DoS |
| `pip` | 24.0 | CVE-2025-8869 | 25.3+ | Arbitrary file overwrite |
| `setuptools` | 68.1.2 | CVE-2024-6345 | 70.0.0+ | Remote code execution |

**Action Required**:
```bash
pip install --upgrade cryptography>=43.0.1 setuptools>=78.1.1 urllib3>=2.6.0 pip>=25.3
```

### 1.2 Hardcoded Credentials in Docker Compose (HIGH - 6 issues)

| File | Line | Issue | Fix |
|------|------|-------|-----|
| `infra/compose.yaml` | 24 | `MINIO_ACCESS_KEY=minioadmin` | Use `${MINIO_ACCESS_KEY}` |
| `infra/compose.yaml` | 25 | `MINIO_SECRET_KEY=minioadmin` | Use `${MINIO_SECRET_KEY}` |
| `infra/compose.yaml` | 104 | `POSTGRES_PASSWORD=apex` | Use `${POSTGRES_PASSWORD}` |
| `infra/compose.yaml` | 165 | `MINIO_ROOT_PASSWORD=minioadmin` | Use `${MINIO_ROOT_PASSWORD}` |
| `infra/compose.yaml` | 183 | `OPENSEARCH_INITIAL_ADMIN_PASSWORD=...` | Use `${OPENSEARCH_PASSWORD}` |
| `infra/compose.yaml` | 210 | `GF_SECURITY_ADMIN_PASSWORD=admin` | Use `${GRAFANA_PASSWORD}` |

**Note**: These are acceptable for local development but MUST use env vars for production.

### 1.3 Incomplete Integrations (HIGH - 8 issues)

| File | Line | TODO | Priority |
|------|------|------|----------|
| `services/worker/tasks.py` | 103 | PM system API integration pending | High |
| `services/worker/tasks.py` | 152 | Email service integration pending | High |
| `modules/intelligence/__init__.py` | 61 | CostPredictor not imported | High |
| `modules/intelligence/__init__.py` | 104 | LaborPredictor not imported | High |
| `modules/quoting/__init__.py` | 245 | Cost prediction not wired | High |
| `services/api/routes/crm.py` | 51 | Webhook signature validation | High |
| `services/api/utils/wind_data.py` | 84 | NOAA ASOS lookup not implemented | Medium |
| `modules/rag/__init__.py` | 116-222 | Gemini response parsing incomplete | Medium |

### 1.4 Hardcoded Database URLs (HIGH - 5 issues)

| File | Line | Issue |
|------|------|-------|
| `services/api/scripts/seed_defaults.py` | 25 | `postgresql://apex:apex@localhost:5432/apex` |
| `services/api/scripts/generate_test_data.py` | 126 | Same hardcoded URL |
| `services/api/scripts/seed_aisc_sections.py` | 26 | Same hardcoded URL |
| `services/api/routes/poles_aisc.py` | 21 | Same hardcoded URL |
| `services/api/routes/monument.py` | 29 | Same hardcoded URL |

**Fix**: Replace with `os.getenv("DATABASE_URL", "...")`

---

## 2. Medium Priority Issues

### 2.1 Placeholder Implementations (19 items)

**Worker Tasks** (`services/worker/`):
- `tasks.py:104` - Placeholder project number generation
- `tasks.py:128` - PM ref using placeholder value
- `tasks.py:153` - Email logging instead of sending

**ML Domain** (`services/api/src/apex/domains/signage/`):
- `edge_cases_advanced.py:56` - Hardcoded wind force estimate (1000.0)
- `edge_cases_advanced.py:99` - Placeholder weight distribution
- `ml_models.py:88` - Model loading placeholder
- `ml_models.py:121` - Random training placeholder
- `ml_models.py:148` - Placeholder prediction
- `performance.py:126` - Feature hashing placeholder
- `performance.py:204` - Model quantization placeholder
- `engineering_docs.py:190` - LaTeX compilation not implemented

**Modules** (`modules/`):
- `workflow/__init__.py:114` - Email monitoring not implemented
- `rag/__init__.py:116,181,216,222,290` - Gemini parsing incomplete
- `engineering/__init__.py:41,73,94` - APEX routes not imported
- `quoting/__init__.py:207,375,435,465` - Various features pending

### 2.2 Code Quality Issues

| File | Issue |
|------|-------|
| `services/api/alembic/env.py:3` | Import block unsorted (ruff I001) |
| `services/api/alembic/versions/001_foundation.py:32` | Import block unsorted (ruff I001) |

---

## 3. Low Priority Issues

### 3.1 Test Fixtures Using Mock Data (Acceptable)

Files in `tests/` directories appropriately use mock/sample data:
- `services/ml/tests/test_pdf_extractor.py` - Uses `sample_pdf_text` fixture
- `services/ml/tests/test_cost_model.py` - Uses `sample_training_data` fixture
- `services/api/tests/conftest.py` - Mock Redis/MinIO/Celery clients

**Status**: No action required - test mocks are appropriate.

### 3.2 MockAuth for Development (Acceptable)

- `services/api/src/apex/api/auth.py:247` - `MockAuth` class exists
- Used only when `ENV == "dev"` - appropriate pattern

**Status**: No action required - development helper is properly gated.

---

## 4. Remediation Plan

### Phase 1: Critical Security Fixes (Immediate)

```bash
# 1. Upgrade vulnerable dependencies
cd services/api
pip install cryptography>=43.0.1 setuptools>=78.1.1 urllib3>=2.6.0

# 2. Update requirements
pip freeze | grep -E "cryptography|setuptools|urllib3" > requirements-security.txt
```

### Phase 2: Environment Variable Migration (Day 1)

1. Create `.env.example` with all required variables
2. Update `infra/compose.yaml` to use `${VAR}` syntax
3. Update hardcoded database URLs in scripts

### Phase 3: Integration Completion (Day 2-3)

1. Wire email service (SendGrid/SES)
2. Wire PM system API
3. Complete Gemini response parsing
4. Import CostPredictor/LaborPredictor

### Phase 4: Testing Validation (Day 3-4)

1. Run full test suite with 80% coverage gate
2. Run contract tests
3. Run k6 performance tests

---

## 5. Security Scan Summary

| Tool | Status | Issues |
|------|--------|--------|
| **pip-audit** | Ran | 9 vulnerabilities in 4 packages |
| **Ruff** | Ran | 2 import ordering issues |
| **Semgrep** | Configured in CI | Runs on push/PR |
| **Gitleaks** | Configured in CI | Runs on push/PR |
| **Trivy** | Configured in CI | Container scanning |

---

## Next Steps

1. **Fix critical dependency vulnerabilities** (cryptography, setuptools, urllib3)
2. **Migrate hardcoded credentials to environment variables**
3. **Complete high-priority integrations** (email, PM system)
4. **Run full test suite**
5. **Deploy to staging for validation**
