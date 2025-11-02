# Frontend Integration Notes - Iteration 3

## Envelope Integration Status

### ✅ Completed Features

1. **Enhanced Envelope Parsing** (`src/utils/envelope.ts`)
   - Full parsing of `ResponseEnvelope` with all fields
   - Extraction of `warnings`, `errors`, `confidence`
   - `constants_version` from `trace.constants_version`
   - `content_sha256` for caching/verification
   - Confidence level categorization (high/medium/low)
   - Review requirement detection (confidence < 0.5)

2. **API Client Enhancements** (`src/api/client.ts`)
   - Idempotency key support with localStorage persistence
   - Cache control headers with `content_sha256` (If-None-Match)
   - Full error handling with field-level errors and warnings
   - All new endpoints: file upload, task polling, project events

3. **Real-Time Derive Integration** (`src/components/InteractiveCanvas.tsx`)
   - Debounced 300ms derive on canvas transform
   - Confidence badge display (green/yellow/red)
   - Warning display in Snackbar
   - Form updates from backend-derived values
   - Content SHA256 caching
   - Low confidence warnings

4. **Async Task Polling** (`src/hooks/useTaskPolling.ts`, `src/components/TaskProgress.tsx`)
   - Polling every 2s for task status
   - Progress bar display (0-100%)
   - Success/error handling with callbacks
   - Max attempts (150 = 5 minutes)
   - Automatic cleanup

5. **Error Boundaries & Validation**
   - `ErrorBoundary` component wrapping stages
   - Field-level error display from `envelope.errors`
   - Engineering review flags when confidence < 0.5
   - Baseplate check validation with red borders for failures
   - Submission confirmation with confidence display

6. **File Upload Enhancement** (`src/components/FileUpload.tsx`)
   - Presigned URL workflow: GET `/files/presign` → PUT to MinIO → POST `/files/attach`
   - SHA256 verification with visual indicator
   - Upload progress bar per file
   - File list with verification badges
   - Error handling per file

7. **Idempotency Support** (`src/utils/envelope.ts`)
   - UUID generation for idempotency keys
   - localStorage persistence: `idempotency-{projectId}`
   - Retry with same key on network failure
   - Clear on successful submission

8. **Performance Optimizations**
   - `React.memo` on `InteractiveCanvas`, `PDFPreview`
   - `React.lazy()` for all stage components
   - Debounced autosave utility (1000ms ready)
   - Content SHA256 caching for derive requests

9. **Advanced UI Features**
   - **Confidence Badge**: Color-coded (green/yellow/red) with tooltip
   - **Envelope Footer**: Shows `constants_version`, `git_sha`, `build_id`
   - **Task Progress**: Real-time polling with progress bar
   - **Warning Display**: Toast notifications for all warnings
   - **Review Flags**: Visual indicators for low confidence

### API Integration Details

#### Envelope Structure
```typescript
interface ResponseEnvelope<T> {
  result: T | null;
  assumptions: string[];
  warnings?: string[];  // NEW
  errors?: Array<{ field: string; message: string }>;  // NEW
  confidence: number;
  content_sha256?: string;  // NEW
  trace: {
    data: { inputs, intermediates, outputs };
    code_version: { git_sha, dirty, build_id? };
    constants_version?: string;  // NEW
    model_config: { provider, model, temperature, max_tokens, seed? };
  };
}
```

#### New Endpoints Integrated
- `GET /projects/{id}/events` - Project event timeline
- `POST /projects/{id}/files/presign` - Get presigned upload URL
- `POST /projects/{id}/files/attach` - Attach uploaded file
- `GET /projects/{id}/files` - List project files
- `POST /projects/{id}/report` - Generate report (returns task_id)
- `GET /tasks/{task_id}` - Poll task status
- `POST /projects/{id}/submit` - Submit with idempotency

### Error Handling Flow

1. **API Error** → Parse envelope → Extract warnings/errors
2. **Field Errors** → Display in toast + inline validation
3. **Warnings** → Toast notification (warning severity)
4. **Low Confidence** → Warning toast + review flag
5. **Network Error** → Retry with stored idempotency key

### Real-Time Features

#### Canvas Derive Flow
1. User drags/resizes canvas
2. `onTransformEnd` fires
3. Debounce 300ms
4. POST `/cabinets/derive` with `If-None-Match: {sha256}`
5. Parse envelope:
   - Extract `result` → Update form
   - Extract `warnings` → Toast notifications
   - Extract `confidence` → Update badge
   - Extract `content_sha256` → Store for next request
6. Visual feedback: Loading indicator, confidence badge, warnings

#### Task Polling Flow
1. POST `/projects/{id}/report` → `{task_id: "..."}`
2. Poll GET `/tasks/{task_id}` every 2s
3. Display progress: `status.progress` (0-100%)
4. On `completed`: Download PDF, show success
5. On `failed`: Show error, retry button

### File Upload Flow

1. User selects file(s)
2. For each file:
   - POST `/files/presign` → `{url, key, expires_in}`
   - Compute SHA256 hash
   - PUT file to presigned URL (with progress)
   - POST `/files/attach` → `{key, sha256, filename}`
3. Display file list with verification badges
4. Show SHA256 hash (truncated) for verification

### Validation & Gates

**Per-Stage Validation:**
- `validateStage('cabinet', projectData)` → `{isValid, errors[]}`
- Visual indicators in stepper
- Red borders on failing baseplate checks
- Engineering review flag when confidence < 0.5

**Submission Gates:**
- Validate all required stages
- Check overall confidence
- Confirmation dialog with confidence badge
- Idempotency key for retry safety

### Performance Metrics

**Code Splitting:**
- Initial bundle: ~150KB
- Stage components: +20KB per stage (lazy loaded)
- Canvas + Konva: ~80KB

**Caching:**
- Content SHA256 cache keys
- GET requests with `Cache-Control: max-age=300`
- Idempotency keys persisted in localStorage

**Debouncing:**
- Canvas derive: 300ms
- Autosave: 1000ms (utility ready)

### Known Limitations

1. **WebSocket**: Not implemented, using polling fallback
2. **PDF Preview**: Requires actual report generation endpoint
3. **File Deletion**: DELETE endpoint not yet implemented
4. **Compare Mode**: Side-by-side diff not implemented
5. **What-if Sliders**: Live updates not implemented

### Testing Checklist

- [ ] Canvas derive triggers API call with correct debounce
- [ ] Confidence badge displays correct color
- [ ] Warnings show in toast notifications
- [ ] Field errors display inline
- [ ] Task polling shows progress correctly
- [ ] File upload with SHA256 verification works
- [ ] Idempotency key persists and retries work
- [ ] Error boundaries catch React errors
- [ ] Baseplate checks show red borders on failure
- [ ] Submission confirmation shows confidence
- [ ] Envelope footer displays trace info

### Next Steps

1. Implement WebSocket for long-running tasks (optional)
2. Add compare mode for project variants
3. Implement what-if sliders for live updates
4. Add export button for project JSON
5. Enhance error messages with trace data
6. Add retry logic for transient failures

### Coordination Notes

**With Agent 2:**
- Verify `warnings` and `errors` fields in envelope
- Confirm `constants_version` location in trace
- Validate `content_sha256` for caching

**With Agent 4:**
- Sync warning types and messages
- Coordinate engineering review flags
- Align baseplate check validation

**With Agent 5:**
- Coordinate test fixtures for envelope responses
- Sync error scenarios for testing
