# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

SignX is a comprehensive sign industry platform that combines structural engineering calculations, AI-powered cost estimation, and instant online quoting. The platform specializes in sign calculation workflows with complete audit trails, deterministic calculations, and production-ready engineering features.

**Business Model**: Transform sign manufacturing from "we'll get back to you in 3 days" to "here's your quote in 5 minutes" - the Xometry/SendCutSend model for the sign industry.

## Architecture

The codebase has evolved through multiple phases and contains both legacy and modern architectures:

### Current Architecture (Production)
- **Primary API**: FastAPI backend in `services/api/` with 40+ production endpoints
- **Frontend**: React/Vite app in `ui/`
- **Workers**: Celery async task worker in `services/worker/`
- **Domain Services**: Specialized microservices (signcalc, materials, signs, translator, ml)

### Emerging Architecture (Refactoring in Progress)
- **Platform Core**: Module plugin system in `platform/` (registry, events, unified API)
- **Modules**: Feature modules in `modules/` (engineering, intelligence, workflow, rag, quoting)
- **Goal**: Migrate from monolithic to modular, event-driven architecture

### Key Directories
- `services/api/` - Main FastAPI API server with Alembic migrations (PRODUCTION)
- `services/worker/` - Celery async task worker
- `services/signcalc-service/` - Core sign calculation engine
- `services/ml/` - Machine learning services for cost prediction
- `services/materials-service/` - Material database service
- `services/signs-service/` - Sign-specific domain logic
- `ui/` - React frontend (Vite + MUI + Zustand + React Query)
- `platform/` - New modular platform core (registry, events)
- `modules/` - Plugin modules (engineering, RAG, quoting, intelligence, workflow)
- `infra/` - Docker Compose and deployment configurations
- `tests/` - Comprehensive test suites (unit, integration, contract, e2e, performance)
- `docs/` - Extensive documentation
- `standards/` - Engineering standards (ASCE 7-16, NDDOT, etc.)

## Essential Commands

### Development Setup
```bash
# Start all services
cd infra
docker-compose up -d

# Run database migrations
cd ../services/api
alembic upgrade head

# Health check
curl http://localhost:8000/health
```

### Frontend Development
```bash
cd ui
npm install
npm run dev          # Start development server (Vite)
npm run build        # Production build
npm run lint         # ESLint check
```

### Backend Development
```bash
# Lint Python code
ruff check .

# Run all tests
pytest -v

# Run specific test suites
pytest tests/unit/ -v
pytest tests/service/ -v
pytest tests/e2e/ -v
pytest tests/contract/ -v

# Run smoke test
python scripts/smoke.py
```

### Using Make (from root)
```bash
make up              # Start services
make down            # Stop services
make logs            # View API logs
make install         # Install base dependencies
make install-ml      # Install ML/AI dependencies
make test            # Run core tests
make test-ml         # Run ML pipeline tests
make lint            # Run linter on core code
make lint-ml         # Run linter on ML code
make format          # Format code with black
make clean           # Clean build artifacts
make all             # Run linter and tests
```

### Database Operations
```bash
# Create new migration
cd services/api
alembic revision -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### ML Pipeline (AI/ML Features)
```bash
# Extract cost data from PDFs
make extract-pdfs

# Train cost prediction model
make train-cost-model

# Test AI predictions
make test-predictions

# Full ML pipeline
make ml-pipeline
```

## Key Development Principles

1. **Determinism**: All calculations must be pure functions - same inputs always produce same outputs
2. **Test-First**: Write tests before implementing features
3. **Envelope Pattern**: All API responses follow standardized envelope format with audit trails
4. **Graceful Degradation**: Services fallback when dependencies are unavailable
5. **Idempotency**: Critical operations use idempotency keys to prevent duplicates
6. **PE Compliance**: All engineering calculations must be accurate, documented, and traceable for Professional Engineer stamping

## Service Dependencies

- **PostgreSQL** (port 5432): Primary database with pgvector extension
- **Supabase PostgreSQL** (port 5433): Authentication and user management database
- **Redis** (port 6379): Caching and Celery queue
- **MinIO** (ports 9000/9001): S3-compatible object storage
- **OpenSearch** (port 9200): Search with DB fallback
- **OpenSearch Dashboards** (port 5601): Search visualization
- **Grafana** (port 3001): Monitoring and metrics (admin/admin)
- **Postgres Exporter** (port 9187): PostgreSQL metrics for Prometheus

## Testing Strategy

The test pyramid includes:
- **Unit Tests**: Pure function validation, determinism checks
- **Integration Tests**: API route validation, service interaction
- **Contract Tests**: Envelope consistency, OpenAPI compliance
- **E2E Tests**: Full workflow validation from UI to database
- **Performance Tests**: Solver benchmarks, load testing with k6
- **Security Tests**: Vulnerability scanning, auth testing
- **Regression Tests**: Prevent known bugs from reoccurring
- **Compliance Tests**: Engineering standard validation (ASCE 7-22, ACI 318, AISC)

Run tests with proper fixtures:
```bash
pytest -v --tb=short  # Verbose with short traceback
pytest -k "test_name" # Run specific test
pytest -m "not slow"  # Skip slow tests
pytest --cov          # Run with coverage report
```

## Common Workflows

### Adding a New API Endpoint (Legacy API)
1. Define schema in `services/api/src/apex/api/schemas.py`
2. Implement route in appropriate file under `services/api/src/apex/api/routes/`
3. Add unit tests in `tests/unit/`
4. Add integration tests in `tests/service/`
5. Update OpenAPI documentation
6. Ensure envelope pattern is used for responses

### Adding a New Module (New Platform)
1. Create module directory in `modules/my_module/`
2. Define `ModuleDefinition` with name, version, API prefix
3. Create FastAPI router with module routes
4. Subscribe to relevant events via event bus
5. Register module with platform registry
6. Add module documentation
7. Write comprehensive tests

### Modifying Database Schema
1. Create migration: `cd services/api && alembic revision -m "description"`
2. Edit migration file in `services/api/alembic/versions/`
3. Test migration: `alembic upgrade head`
4. Test rollback: `alembic downgrade -1`
5. Add rollback test to test suite

### Frontend Component Development
1. Create component in `ui/src/components/`
2. Follow existing patterns for state management (Zustand stores)
3. Use MUI components for consistency
4. Add accessibility attributes
5. Use React Query for API calls
6. Add proper TypeScript types

## Configuration

Environment variables are managed through:
- `infra/compose.yaml` - Docker Compose defaults
- `.env` files (not committed) - Local overrides
- `env.example` - Template for environment variables
- `services/api/src/apex/api/deps.py` - Settings validation

Critical settings:
- `DATABASE_URL` - PostgreSQL connection (main database)
- `REDIS_URL` - Redis connection
- `MINIO_URL` - Object storage endpoint
- `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` - MinIO credentials
- `APEX_SUPABASE_URL` / `APEX_SUPABASE_KEY` - Supabase auth (optional)
- `GEMINI_API_KEY` - Google Gemini API for RAG features
- `ANTHROPIC_API_KEY` - Claude API (optional)

## Monitoring & Debugging

- **API Docs**: http://localhost:8000/docs (OpenAPI/Swagger)
- **Health Check**: http://localhost:8000/health
- **Ready Check**: http://localhost:8000/ready
- **Frontend**: http://localhost:3000 (Vite dev server)
- **Grafana**: http://localhost:3001 (admin/admin)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **OpenSearch Dashboards**: http://localhost:5601
- **PostgreSQL**: localhost:5432 (apex/apex)
- **Supabase DB**: localhost:5433 (supabase/your-super-secret-password)

## Error Handling Patterns

The codebase uses structured error responses with the envelope pattern:
```python
# Services return envelopes with error details
{
    "ok": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input",
        "details": {...}
    },
    "metadata": {
        "timestamp": "2025-11-15T...",
        "request_id": "abc123",
        "audit": {...}
    }
}
```

Always check `ok` field before accessing `result` in responses. All production code should use the `make_envelope()` helper from `services/api/src/apex/api/common/models.py`.

## Tech Stack

### Backend
- **Language**: Python 3.12
- **API Framework**: FastAPI 0.110+
- **Database ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Task Queue**: Celery + Redis
- **Validation**: Pydantic v2

### Frontend
- **Framework**: React 19
- **Build Tool**: Vite 7
- **UI Library**: Material-UI (MUI) 7
- **State Management**: Zustand 5
- **Data Fetching**: TanStack React Query 5
- **Forms**: React Hook Form + Zod validation
- **Language**: TypeScript 5.9

### AI/ML
- **RAG**: Google Gemini File Search (multimodal, free queries)
- **Reasoning**: Claude Sonnet 4.5 (200K context, extended thinking)
- **Cost Prediction**: XGBoost 2.1.4 (GPU-accelerated)
- **Orchestration**: LangGraph (multi-agent workflows)
- **Environment**: Conda (environment-ml.yml)

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Database**: PostgreSQL 16 with pgvector extension
- **Cache**: Redis 7
- **Storage**: MinIO (S3-compatible)
- **Search**: OpenSearch 2.12
- **Monitoring**: Grafana + Prometheus exporters
- **Logging**: Structured logs + Sentry (optional)

## Key Documentation Files

Start with these documents for understanding the project:
- **README.md** - Project overview and business context
- **GETTING_STARTED.md** - Setup and onboarding guide
- **ARCHITECTURE_OVERVIEW.md** - System architecture and modules
- **DEEP_REFACTORING_PLAN.md** - Migration from monolith to modular architecture
- **INTEGRATION_PLAN.md** - Technical roadmap
- **API_ENDPOINTS_REFERENCE.md** - Complete API documentation
- **DEPLOYMENT_GUIDE.md** - Production deployment instructions

## Important Notes

### Naming Conventions
- The project is called **SignX** (or SignX Platform/SignX-Studio)
- Legacy code may reference "APEX" (the original name for the engineering module)
- Database and some services use "apex" as identifiers (this is correct, don't change)

### Two Architectures Coexist
- **Legacy (Production)**: `services/api/` - monolithic, tightly coupled, 40+ working endpoints
- **New (In Development)**: `platform/` + `modules/` - modular, event-driven, plugin architecture
- When adding features, prefer the new modular architecture
- Don't break existing production code in `services/api/`

### Frontend Locations
- **Primary Frontend**: `ui/` (React + Vite, actively developed)
- **Legacy References**: Some docs mention `apex/apps/ui-web/` (may be outdated)

### PE Compliance Requirements
All engineering calculations must:
- Be deterministic (same inputs = same outputs)
- Include proper code citations (ASCE 7-22, ACI 318, AISC 360)
- Provide complete audit trails
- Include proper unit handling and validation
- Be validated against known test cases

Always check `PE_REVIEW_CHECKLIST.md` before implementing calculation features.

## Development Workflow

1. **Clone and Setup**
   ```bash
   git clone <repo-url>
   cd SignX
   cp env.example .env
   # Edit .env with your API keys
   ```

2. **Start Infrastructure**
   ```bash
   make up
   # Wait for all services to be healthy
   ```

3. **Run Migrations**
   ```bash
   cd services/api
   alembic upgrade head
   ```

4. **Start Frontend**
   ```bash
   cd ui
   npm install
   npm run dev
   ```

5. **Verify Setup**
   - API: http://localhost:8000/docs
   - Frontend: http://localhost:3000
   - Run: `make all` to verify tests pass

## Getting Help

- **Documentation**: Check the `docs/` directory and `.md` files in root
- **API Reference**: http://localhost:8000/docs when services are running
- **Architecture Questions**: See ARCHITECTURE_OVERVIEW.md
- **Deployment**: See DEPLOYMENT_GUIDE.md
- **Common Issues**: See GETTING_STARTED.md troubleshooting section

---

**Built for Eagle Sign Co. | Powered by 95 years of expertise + 2025 AI**
