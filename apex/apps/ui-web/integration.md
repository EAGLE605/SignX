# Frontend-Backend Integration Notes

## API Integration Status

### ✅ Completed

1. **API Client Layer** (`src/api/client.ts`)
   - Full `ResponseEnvelope<T>` parsing with error handling
   - Custom `APIError` class with status codes and envelope data
   - All CalcuSign endpoints integrated:
     - Projects (list, get, create)
     - Site resolution
     - Cabinet derive
     - Pole options
     - Pricing estimate
     - Foundation solve/checks

2. **Real-Time Canvas Integration**
   - `InteractiveCanvas` component with debounced derive calls
   - 300ms debounce on `onTransformEnd` → POST `/cabinets/derive`
   - Two-way binding: canvas changes trigger API, API results update form
   - Loading states with visual indicators
   - AbortController for request cancellation

3. **Error Handling**
   - `ErrorBoundary` for React error catching
   - `Toast` provider with Snackbar notifications
   - User-friendly error messages from envelope assumptions
   - 4xx/5xx handled with appropriate toast severity

4. **Validation & Gates**
   - `validateStage()` utility for per-stage validation
   - Visual indicators in stepper (red outline for incomplete stages)
   - Confirmation dialog before project submission
   - Required field validation before stage completion

5. **Performance Optimizations**
   - `React.memo` on `InteractiveCanvas` and `PDFPreview`
   - Lazy loading with `React.lazy()` for all stage components
   - Debounced autosave (1000ms) utility ready
   - Code splitting reduces initial bundle size

6. **Optimistic Updates**
   - Project creation shows immediate feedback
   - Rollback on failure
   - Loading states during async operations

### API Endpoint Mapping

| Frontend Component | API Endpoint | Method | Status |
|-------------------|--------------|--------|--------|
| `ProjectList` | `/projects` | GET | ✅ |
| `ProjectList` | `/projects` | POST | ✅ |
| `OverviewStage` | `/projects/{id}` | GET | ✅ |
| `SiteStage` | `/signage/common/site/resolve` | POST | ✅ |
| `CabinetStage` | `/signage/common/cabinets/derive` | POST | ✅ |
| `InteractiveCanvas` | `/signage/common/cabinets/derive` | POST | ✅ (debounced) |
| `StructuralStage` | `/signage/common/poles/options` | POST | ✅ |
| `FoundationStage` | `/signage/direct_burial/footing/solve` | POST | ✅ |
| `FoundationStage` | `/signage/baseplate/checks` | POST | ✅ |
| `FinalizationStage` | `/projects/{id}/estimate` | POST | ✅ |
| `SubmissionStage` | `/projects/{id}/submit` | POST | 🟡 (stub) |

### Response Envelope Handling

All API calls expect and handle the standardized envelope:

```typescript
interface ResponseEnvelope<T> {
  result: T | null;
  assumptions: string[];
  confidence: number;
  trace: { ... };
}
```

**Error Cases:**
- `result === null` + `confidence < 0.5` → APIError with assumptions
- HTTP 4xx/5xx → APIError with status code
- Network errors → APIError with network message

**Success Cases:**
- `result !== null` → Use result data
- `assumptions.length > 0` → Show as info toast (optional)
- `confidence < 1.0` → Consider showing warning (optional)

### Real-Time Features

#### Canvas Derive Integration

```typescript
// Debounced derive on canvas transform
const debouncedDerive = debounce(async (dimensions) => {
  const response = await api.deriveCabinet({
    width_in: Math.round(dimensions.width),
    height_in: Math.round(dimensions.height),
    depth_in: 12,
    density_lb_ft3: 50,
  });
  
  // Update form with backend-derived values
  setRectSize(updated);
}, 300);
```

**Flow:**
1. User drags/resizes canvas shape
2. `onTransformEnd` fires
3. Debounce waits 300ms
4. API call to `/cabinets/derive`
5. Response updates form inputs
6. Toast notification shown

#### WebSocket Support (Future)

For long-running calculations:
- Fallback to polling if WebSocket unavailable
- Status endpoint: `/projects/{id}/status`
- Poll every 2s until `status === 'complete'`

### Validation Gates

**Per-Stage Validation:**

```typescript
validateStage('cabinet', projectData)
// Returns: { isValid: boolean, errors: string[] }
```

**Visual Indicators:**
- ✅ Green checkmark = stage complete
- ❌ Red error icon = validation errors
- ⚪ Gray = pending

**Navigation Control:**
- Stepper allows non-linear navigation
- Validation warnings logged but don't block navigation
- Submission requires all stages valid

### Performance Metrics

**Code Splitting:**
- Initial bundle: ~150KB (estimate)
- Stage components lazy-loaded: +20KB per stage
- Canvas + Konva: ~80KB

**Debouncing:**
- Canvas derive: 300ms
- Form autosave: 1000ms (utility ready)

**Memoization:**
- `InteractiveCanvas`: memo wrapped
- `PDFPreview`: memo wrapped
- Stage components: lazy loaded (isolated)

### Testing

**API Mock Responses:**

```typescript
// Mock for testing
const mockEnvelope = {
  result: { area_ft2: 112, weight_lb: 1120 },
  assumptions: [],
  confidence: 1.0,
  trace: { ... }
};
```

**Integration Test Checklist:**
- [ ] Canvas derive triggers API call
- [ ] Error handling shows toast
- [ ] Optimistic updates rollback on failure
- [ ] Validation blocks submission
- [ ] Stage navigation updates URL
- [ ] State persists across refreshes

### Known Limitations

1. **PDF Preview**: Uses placeholder URL, needs actual report generation endpoint
2. **File Upload**: Simulated, needs MinIO presign integration
3. **WebSocket**: Not implemented, polling fallback ready
4. **Submission**: Stub endpoint, needs actual submission logic

### Next Steps

1. Wire PDF generation: `/projects/{id}/report` → `PDFPreview`
2. Integrate file upload: MinIO presign URLs
3. Add WebSocket for long-running calcs (optional)
4. Enhance error messages with trace data
5. Add retry logic for transient failures

### Environment Variables

```env
VITE_API_BASE=/api  # Default proxy to localhost:8000
```

### Coordinate with Agent 2

- Verify endpoint signatures match OpenAPI spec
- Confirm envelope structure for all endpoints
- Sync on error response formats
- Coordinate test fixtures with Agent 5
