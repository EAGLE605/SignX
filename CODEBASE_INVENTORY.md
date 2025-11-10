# SignX Codebase Inventory
## Complete File Structure Reference

### CORE IMPLEMENTATION (services/api) - 4.8 MB
Working production code for sign calculation and project management.

**Key Files:**
- `main.py` - FastAPI application entry point (366 lines)
- `routes/monument.py` - Monument sign API (22,487 lines)
- `routes/poles.py` - Pole selection logic (5,090 lines)
- `routes/poles_aisc.py` - AISC shape filtering (16,260 lines)
- `routes/cantilever.py` - Cantilever design (15,549 lines)
- `routes/direct_burial.py` - Foundation design (6,979 lines)
- `routes/baseplate.py` - Baseplate checks (8,705 lines)
- `routes/pricing.py` - Quote pricing (4,474 lines)
- `routes/auth.py` - Authentication (36,433 lines)
- `domains/signage/` - Core solvers
  - `monument_solver.py` - Wind + structure
  - `cantilever_solver.py` - Cantilever design
  - `asce7_wind.py` - ASCE 7-22 calculations
  - `aisc_database.py` - Steel shape database
- `audit.py` - Audit logging (204 lines)
- `rbac.py` - Role-based access (329 lines)

**Database:**
- `alembic/versions/` - 18 migrations applied
- Tables: projects, project_payloads, project_events, pole_sections

### FRONTEND (apex/apps/ui-web) - 40% Complete
React TypeScript application for design workflow.

**Key Components:**
- `src/components/stages/` - Design stages
  - OverviewStage.tsx - Project intro
  - SiteStage.tsx - Location/wind data
  - CabinetStage.tsx - Sign dimensions
  - StructuralStage.tsx - Pole selection
  - FoundationStage.tsx - Foundation design
  - ReviewStage.tsx - Final review
  - SubmissionStage.tsx - Quote/accept
  - FinalizationStage.tsx - Completion
- `src/components/` - Shared components
  - FileUpload.tsx
  - PDFPreview.tsx
  - ProjectList.tsx
  - ExportDialog.tsx
- `src/lib/api.ts` - API client (auto-generated)
- `src/main.tsx` - React entry point

**Status:** Components built, layout/styling needed

### KNOWLEDGE SYSTEM (scripts/) - 60% Complete
Industry article scraping and knowledge base.

**Active Scripts:**
- `scrape_industry_sites.py` - RSS feed monitoring (15+ sites)
- `scrape_substack_rss.py` - Substack newsletter scraper
- `monitor_industry_news.py` - Continuous monitoring
- `export_to_gemini_rag.py` - Upload to Gemini API
- `setup_gemini_corpus.py` - Corpus generator
- `web_ui.py` - Knowledge browser UI (24KB)

**Database Schema:**
- `database/models.py` - SQLAlchemy models
- `database/db_utils.py` - Database utilities
- `database/init_schema.sql` - SQL schema (12KB)

**Tables:**
- industry_sites - 15 monitored websites
- industry_articles - Scraped content
- topics - Keywords & categorization
- article_topics - Many-to-many
- monitoring_state - State tracking

### MULTI-AGENT ORCHESTRATION (svcs/) - 60% Complete
Event-driven agent framework (still in dev).

**Components:**
- `orchestrator/main.py` - Event dispatcher (295 lines)
- `agent_translator/main.py` - AI orchestration (279 lines)
- `agent_materials/main.py` - Material analysis (251 lines)
- `agent_stackup/main.py` - Stack design (193 lines)
- `agent_dfma/main.py` - Design for mfg (176 lines)
- `agent_signs/main.py` - Sign analysis (115 lines)
- `common/fsqueue.py` - File system queue (76 lines)

**Status:** Framework built, not integrated with main API yet

### DEMO/REFERENCE (apex/) - Stubs Only
Copied from svcs/ to show architecture, not used in production.

- `services/api/` - Stub routes (not real)
- `apps/ui-web/` - Same as apex/apps/ui-web
- `svcs/` - Symlink to root svcs/
- `signcalc/` - Standalone calculators

### DOCUMENTATION (docs/) - Excellent
Comprehensive guides and references (1.1 MB).

**Key Docs:**
- `architecture/` - System design
- `api/` - API endpoint reference
- `deployment/` - Docker/Kubernetes
- `database/` - Schema & migrations
- `getting-started/` - Quick start guide
- `compliance/` - Standards & codes
- `solvers/` - Algorithm documentation
- `integration/` - Third-party integration

### TESTS (tests/) - Good Coverage
Unit, integration, E2E, and contract tests.

- `unit/` - Pure function tests
- `service/` - Domain logic tests
- `integration/` - API endpoint tests
- `e2e/` - Full workflow tests
- `contract/` - Envelope consistency
- `fixtures/` - Test data

### INFRASTRUCTURE (infra/) - Production Ready
Docker Compose, Kubernetes, monitoring (2.2 MB).

**Services Defined:**
- api - FastAPI server
- worker - Celery async tasks
- signcalc - Sign calculator
- db - PostgreSQL 17
- cache - Redis 7
- object - MinIO S3
- search - OpenSearch 2.0

**Monitoring:**
- Prometheus - Metrics collection
- Grafana - Dashboards
- Kibana - OpenSearch UI

**Deployment:**
- `terraform/` - Cloud IaC
- `docker/` - Service Dockerfiles
- `monitoring/` - Prometheus config

### CONFIGURATION
- `.cursorrules` - AI coding rules
- `Makefile` - Common commands
- `pyproject.toml` - Python dependencies
- `package.json` - Node dependencies
- `docker-compose.yml` - Alternative compose

### SIZE DISTRIBUTION
```
services/api           4.8 MB  (REAL IMPLEMENTATION)
docs                   1.1 MB  (Excellent documentation)
infra                  2.2 MB  (Production deployment)
archive                481 KB  (Old code)
scripts                429 KB  (Knowledge tools)
apex                   901 KB  (Stubs/demos)
tests                  273 KB  (Test suites)
svcs                   144 KB  (Agent framework)
artifacts              183 KB  (Demo outputs)
platform               25 KB   (Minimal)
modules                63 KB   (EMPTY)
```

### WHAT TO USE IN PRODUCTION

**Start here:**
1. `/services/api/` - All real endpoint code
2. `/scripts/` - Knowledge system tools
3. `/infra/` - Deployment configs
4. `/tests/` - Test patterns

**Ignore (stubs only):**
1. `/apex/services/` - Not production
2. `/platform/` - Minimal, not used
3. `/modules/` - Empty directory

**In development:**
1. `/apex/apps/ui-web/` - Frontend 40% done
2. `/svcs/` - Agent framework, not integrated
3. `/apex/svcs/` - Duplicate of svcs/

**For reference:**
1. `/docs/` - Excellent architecture docs
2. `/archive/` - Historical code
3. `/info/` - Old notes

---

**Total Codebase:** ~11 MB (with git history)  
**Active Production Code:** ~5 MB  
**Status:** 70% production-ready (calculation + infrastructure working, quoting + integration missing)
