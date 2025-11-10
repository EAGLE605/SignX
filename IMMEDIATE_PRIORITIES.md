# SignX - Immediate Priorities & Action Items
## What to Do Starting Right Now

---

## TLDR: Next 7 Days

```
TODAY (Day 1):
  ✓ Read STRATEGIC_CODEBASE_ANALYSIS.md (30 min)
  ✓ Backup database (10 min)
  ✓ Create /api/v1/quoting/instant endpoint (2 hours)
  ✓ Test locally with curl (30 min)

TOMORROW (Day 2):
  ✓ Add Gemini RAG query to quoting endpoint (1 hour)
  ✓ Wire up React form component (1 hour)
  ✓ Test end-to-end locally (30 min)

DAY 3:
  ✓ Deploy API to Railway (30 min)
  ✓ Deploy frontend to Vercel (30 min)
  ✓ Test on live URLs (30 min)

WEEK 1:
  ✓ Add email sending with Celery (2 hours)
  ✓ Polish quote response format (1 hour)
  ✓ Create landing page (2 hours)
  ✓ Setup analytics (1 hour)
  ✓ Generate 5 test quotes (1 hour)

→ RESULT: Working quote system that customers can use
→ TIME INVESTMENT: 20-25 hours
→ BUSINESS IMPACT: Revenue-generating feature
```

---

## CRITICAL PATH (Must Do)

### 1. CREATE QUOTING ENDPOINT
**File:** `/home/user/SignX/services/api/src/apex/api/routes/quoting.py`

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid

router = APIRouter(prefix="/quoting", tags=["quoting"])

class InstantQuoteRequest(BaseModel):
    customer_name: str
    sign_type: str  # "monument", "channel_letter", "ground_sign"
    dimensions: dict  # {"width_ft": 10, "height_ft": 4}
    location: str
    budget: float = None
    timeline: str = None

@router.post("/instant")
async def instant_quote(req: InstantQuoteRequest):
    """Generate instant quote for customer sign request."""
    
    # TODO: 
    # 1. Call monument_solver (or appropriate solver)
    # 2. Query Gemini RAG for similar projects
    # 3. Calculate pricing
    # 4. Return professional quote JSON
    
    return {
        "quote_id": str(uuid.uuid4()),
        "customer_name": req.customer_name,
        "status": "pending",
        "timestamp": datetime.now().isoformat()
    }
```

**Then register in main.py:**
```python
from .routes.quoting import router as quoting_router
app.include_router(quoting_router)
```

### 2. CREATE WEB FORM
**File:** `/home/user/SignX/apex/apps/ui-web/src/pages/QuotePage.tsx`

```typescript
import React, { useState } from 'react';
import { Box, Button, TextField } from '@mui/material';
import { apiClient } from '../lib/api';

export function QuotePage() {
  const [formData, setFormData] = useState({
    customer_name: '',
    sign_type: 'monument',
    dimensions: { width_ft: 10, height_ft: 4 },
    location: ''
  });
  const [quote, setQuote] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await apiClient.post('/quoting/instant', formData);
      setQuote(response);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <form onSubmit={handleSubmit}>
        <TextField 
          label="Your Name"
          value={formData.customer_name}
          onChange={(e) => setFormData({...formData, customer_name: e.target.value})}
        />
        {/* More fields... */}
        <Button type="submit" disabled={loading}>
          Get Quote
        </Button>
      </form>
      
      {quote && (
        <Box mt={4}>
          <h2>Quote #{quote.quote_id}</h2>
          <pre>{JSON.stringify(quote, null, 2)}</pre>
        </Box>
      )}
    </Box>
  );
}
```

### 3. INTEGRATE RAG
**File:** `/services/api/src/apex/api/services/rag.py` (NEW)

```python
import google.generativeai as genai
from typing import List, Dict

async def query_gemini_similar_projects(
    sign_type: str,
    location: str,
    dimensions: dict
) -> List[Dict]:
    """Query Gemini RAG for similar past projects."""
    
    query = f"""
    Find sign projects similar to:
    - Type: {sign_type}
    - Location: {location}
    - Dimensions: {dimensions['width_ft']}ft x {dimensions['height_ft']}ft
    
    Return: 3-5 most similar past projects with lessons learned
    """
    
    # TODO: Implement Gemini File API query
    # For now, return mock data
    return [
        {
            "project_name": "Valley Church Monument Sign",
            "dimensions": "10ft x 4ft",
            "location": "Grimes, IA",
            "cost": "$4,500",
            "lead_time_days": 14,
            "lessons": ["Wind load critical in this area", "Direct burial works well here"]
        }
    ]
```

**Then update quoting endpoint:**
```python
from ..services.rag import query_gemini_similar_projects

@router.post("/instant")
async def instant_quote(req: InstantQuoteRequest):
    # ... existing code ...
    
    # Get similar projects
    similar = await query_gemini_similar_projects(
        req.sign_type,
        req.location,
        req.dimensions
    )
    
    # ... rest of implementation ...
    return {
        "quote_id": str(uuid.uuid4()),
        "similar_projects": similar,
        "confidence": 0.85
    }
```

### 4. ADD EMAIL SENDING
**File:** `/services/api/src/apex/worker/tasks/quote_email.py` (NEW)

```python
from celery import shared_task
import smtplib
from email.mime.text import MIMEText

@shared_task(bind=True, max_retries=3)
def send_quote_email(self, quote_id: str, customer_email: str, quote_data: dict):
    """Send quote email to customer."""
    
    try:
        html_body = f"""
        <h1>Your Quote #{quote_id}</h1>
        <p>Thank you for requesting a quote!</p>
        <h2>Design Summary</h2>
        <pre>{quote_data}</pre>
        <p>This quote is valid for 30 days.</p>
        """
        
        msg = MIMEText(html_body, 'html')
        msg['Subject'] = f"Your Monument Sign Quote #{quote_id}"
        msg['From'] = "quotes@eaglesign.net"
        msg['To'] = customer_email
        
        # TODO: Configure SMTP settings
        # smtp.sendmail(...)
        
        return {"status": "sent", "quote_id": quote_id}
        
    except Exception as exc:
        # Retry in 60 seconds
        raise self.retry(exc=exc, countdown=60)
```

---

## WEEK 1 PRIORITIES (In Order)

### Priority 1: Get Quoting Working (Today - Day 1)
- [ ] Create /quoting/instant endpoint stub (2 hours)
- [ ] Create React form (1 hour)
- [ ] Test locally (30 min)
- **Deliverable:** Customer submits form → Gets JSON response

### Priority 2: Add Knowledge Context (Day 2)
- [ ] Implement Gemini RAG query (1 hour)
- [ ] Add similar projects to quote (30 min)
- [ ] Test with real Gemini API (30 min)
- **Deliverable:** Quotes include "based on X similar projects"

### Priority 3: Deploy to Live (Day 3)
- [ ] Deploy API to Railway (30 min)
- [ ] Deploy frontend to Vercel (30 min)
- [ ] Test on live URLs (30 min)
- **Deliverable:** quote.eaglesign.net works from anywhere

### Priority 4: Email Integration (Day 4-5)
- [ ] Setup email service (Resend/Mailgun) (30 min)
- [ ] Create email template (1 hour)
- [ ] Add Celery task (1 hour)
- [ ] Test email delivery (30 min)
- **Deliverable:** Customers receive quote via email

### Priority 5: Polish & Launch (Day 6-7)
- [ ] Improve form UX (better inputs, validations) (2 hours)
- [ ] Add design preview/visualization (2 hours)
- [ ] Create landing page (1 hour)
- [ ] Setup analytics (30 min)
- [ ] Manual testing with 5 test cases (1 hour)
- **Deliverable:** Professional, working quote system

---

## QUICK REFERENCE: KEY FILES

### Production Code to Build From
```
/home/user/SignX/services/api/src/apex/api/
├── routes/monument.py          <- Copy structure for quoting.py
├── routes/pricing.py           <- Use pricing logic
├── routes/direct_burial.py     <- Similar pattern
├── domains/signage/            <- Solvers are here
│   ├── monument_solver.py
│   ├── asce7_wind.py
│   └── aisc_database.py
├── common/models.py            <- ResponseEnvelope pattern
├── worker/tasks/               <- Pattern for email tasks
└── main.py                     <- Register routes here
```

### Frontend Code to Update
```
/home/user/SignX/apex/apps/ui-web/src/
├── pages/
│   └── QuotePage.tsx          <- Create this
├── components/
│   ├── QuoteForm.tsx          <- Create this
│   └── QuoteResults.tsx        <- Create this
├── lib/
│   └── api.ts                 <- Hook up quoting endpoint
└── main.tsx                   <- Add route
```

### Knowledge System Scripts
```
/home/user/SignX/scripts/
├── export_to_gemini_rag.py    <- Use this to upload docs
├── web_ui.py                  <- Knowledge browser (optional)
└── database/
    ├── models.py              <- Industry article DB models
    └── db_utils.py            <- Database utilities
```

---

## ESTIMATED TIMELINE

| Task | Hours | Days | Status |
|------|-------|------|--------|
| Create /quoting/instant endpoint | 2 | Day 1 | CRITICAL |
| Create React form | 1 | Day 1 | CRITICAL |
| Local testing | 1 | Day 1 | CRITICAL |
| Add RAG integration | 1 | Day 2 | HIGH |
| Deploy to Railway | 0.5 | Day 3 | HIGH |
| Deploy to Vercel | 0.5 | Day 3 | HIGH |
| Email integration | 2.5 | Day 4-5 | MEDIUM |
| Polish & improve | 4 | Day 6-7 | NICE-TO-HAVE |
| **TOTAL MVP** | **12 hours** | **3 days** | READY NOW |
| **With Polish** | **20 hours** | **7 days** | PROFESSIONAL |

---

## ARCHITECTURE: What Connects to What

```
Customer
  ↓
Web Form (React)
  ↓
POST /quoting/instant (FastAPI)
  ├→ Monument Solver (calculate structure)
  ├→ Gemini RAG Query (find similar projects)
  ├→ Pricing Service (calculate cost)
  └→ Make Envelope (format response)
  ↓
JSON Quote Response
  ↓
Celery Task Queue
  ↓
Send Email (with quote)
  ↓
Customer Email
```

---

## COMMANDS TO RUN

### 1. Start Development Environment
```bash
cd /home/user/SignX
docker-compose up -d          # Start all services
sleep 30                      # Wait for startup
curl http://localhost:8000/health | jq
```

### 2. Create New Endpoint
```bash
# Edit /services/api/src/apex/api/routes/quoting.py
# Add your endpoint code
# Test locally:
curl -X POST http://localhost:8000/quoting/instant \
  -H "Content-Type: application/json" \
  -d '{"customer_name": "Test", "sign_type": "monument", ...}'
```

### 3. Deploy to Production
```bash
# API to Railway
git push railway main

# Frontend to Vercel
cd apex/apps/ui-web
npm run build
vercel deploy
```

---

## SUCCESS CRITERIA (MVP)

When done, you should be able to:

- [ ] Customer visits web URL
- [ ] Customer fills out form (name, location, dimensions, etc.)
- [ ] Customer clicks "Get Quote"
- [ ] System queries Gemini RAG for similar projects
- [ ] System calculates engineering + pricing
- [ ] System returns professional quote on screen
- [ ] System sends quote via email
- [ ] Customer can accept/reject quote
- [ ] System creates project in database

---

## DON'T DO (Waste of Time Now)

- [ ] Kubernetes setup - Use Docker Compose for now
- [ ] Full AI/ML pipeline - Use simple rules for MVP
- [ ] Multi-agent orchestration - Keep it simple with FastAPI
- [ ] Mobile app - Web responsive design is enough
- [ ] Advanced visualizations - Show JSON quote first
- [ ] Inventory integration - Hardcode prices for now
- [ ] CRM integration - Manual for now
- [ ] Report PDF - JSON is enough for MVP

Save these for Month 2.

---

## SUPPORT RESOURCES

**If you get stuck:**

1. Read existing code in `/services/api/src/apex/api/routes/`
2. Copy patterns from `monument.py` or `cantilever.py`
3. Check tests in `/tests/` for examples
4. Review CLAUDE.md for best practices
5. Check ARCHITECTURE_OVERVIEW.md for system design

**External Resources:**
- FastAPI docs: https://fastapi.tiangolo.com
- Pydantic docs: https://docs.pydantic.dev
- React docs: https://react.dev
- Gemini API: https://aistudio.google.com

---

## CHECKPOINTS (Daily)

**Day 1 End:** 
- [ ] /quoting/instant returns sample JSON response
- [ ] React form exists and submits to API
- [ ] Can see quote results on screen

**Day 2 End:**
- [ ] Gemini RAG query returns similar projects
- [ ] Quote response includes similar_projects field
- [ ] Confidence score calculated

**Day 3 End:**
- [ ] API live on Railway
- [ ] Frontend live on Vercel
- [ ] Both talking to each other

**Day 4 End:**
- [ ] Email template created
- [ ] Celery task sends email
- [ ] Received test email from system

**Day 5 End:**
- [ ] All edge cases handled
- [ ] Form validates inputs
- [ ] Error messages helpful
- [ ] Code clean & documented

**Day 7 End:**
- [ ] 5 test quotes generated successfully
- [ ] Emails delivered reliably
- [ ] System runs 24 hours without errors
- [ ] Ready for customer beta

---

**Next Step:** Start building! Create `/services/api/src/apex/api/routes/quoting.py` right now.

**Time Estimate:** 4 hours to first working quote. Go!
