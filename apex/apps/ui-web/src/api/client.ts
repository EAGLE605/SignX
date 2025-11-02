import type {
  Project,
  SiteResolveRequest,
  SiteResolveResponse,
  CabinetDeriveRequest,
  CabinetDeriveResponse,
  PoleOptionsRequest,
  PricingEstimateRequest,
  PricingEstimateResponse,
} from '../types/api';
import type {
  ResponseEnvelope as FullEnvelope,
  TaskStatus,
  FileUploadResponse,
  FileAttachment,
  ProjectEvent,
} from '../types/envelope';
import { parseEnvelope } from '../utils/envelope';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public envelope?: FullEnvelope,
    public warnings?: string[],
    public fieldErrors?: Array<{ field: string; message: string }>,
    public etag?: string, // ETag for 412 conflicts
  ) {
    super(message);
    this.name = 'APIError';
  }
}

async function request<T>(
  endpoint: string,
  options?: RequestInit & {
    idempotencyKey?: string;
    useCache?: boolean;
    etag?: string; // For optimistic locking
  },
): Promise<FullEnvelope<T>> {
  const url = `${API_BASE}${endpoint}`;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-API-Version': 'v1',
    ...((options?.headers as Record<string, string>) || {}),
  };

  // Add idempotency key if provided
  if (options?.idempotencyKey) {
    headers['Idempotency-Key'] = options.idempotencyKey;
  }

  // Add ETag for optimistic locking (If-Match header)
  if (options?.etag) {
    headers['If-Match'] = options.etag;
  }

  // Add cache control if requested
  if (options?.useCache) {
    headers['Cache-Control'] = 'max-age=300';
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle 412 Precondition Failed (ETag conflict)
    if (response.status === 412) {
      const envelope: FullEnvelope | undefined = await response.json().catch(() => undefined);
      const etag = response.headers.get('ETag') || undefined;
      throw new APIError(
        'Resource was modified by another user. Please refresh and try again.',
        response.status,
        envelope,
        undefined,
        undefined,
        etag,
      );
    }

    if (!response.ok) {
      let envelope: FullEnvelope | undefined;
      try {
        envelope = await response.json();
      } catch {
        // Not JSON response
      }

      const parsed = envelope ? parseEnvelope(envelope) : null;

      throw new APIError(
        parsed?.errors?.[0]?.message || envelope?.assumptions?.join(', ') || `API error: ${response.statusText}`,
        response.status,
        envelope,
        parsed?.warnings,
        parsed?.errors,
      );
    }

    const envelope: FullEnvelope<T> = await response.json();
    const parsed = parseEnvelope(envelope);

    // Validate envelope structure
    if (typeof envelope !== 'object' || envelope === null) {
      throw new APIError('Invalid response format', response.status);
    }

    // Validate required envelope fields
    if (typeof envelope.result === 'undefined') {
      throw new APIError('Missing "result" field in envelope', response.status, envelope);
    }
    if (!Array.isArray(envelope.assumptions)) {
      throw new APIError('Missing or invalid "assumptions" field in envelope', response.status, envelope);
    }
    if (typeof envelope.confidence !== 'number') {
      throw new APIError('Missing or invalid "confidence" field in envelope', response.status, envelope);
    }
    if (!envelope.trace || typeof envelope.trace !== 'object') {
      throw new APIError('Missing or invalid "trace" field in envelope', response.status, envelope);
    }

    // Low confidence with null result is an error
    if (parsed.requiresReview && envelope.result === null) {
      throw new APIError(
        parsed.errors?.[0]?.message || envelope.assumptions.join(', ') || 'Low confidence result requires review',
        response.status,
        envelope,
        parsed.warnings,
        parsed.errors,
      );
    }

    return envelope;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    throw new APIError(
      error instanceof Error ? error.message : 'Network error',
      0,
    );
  }
}

export const api = {
  // Projects
  listProjects: async (): Promise<FullEnvelope<Project[]>> => {
    const envelope = await request<Project[]>('/projects', { useCache: true });
    if (envelope.result && !Array.isArray(envelope.result)) {
      throw new APIError('Invalid project list format', 500, envelope);
    }
    return envelope;
  },

  getProject: async (id: string): Promise<FullEnvelope<Project>> =>
    request<Project>(`/projects/${id}`),

  createProject: async (
    name: string,
    notes?: string,
  ): Promise<FullEnvelope<Project>> =>
    request<Project>('/projects', {
      method: 'POST',
      body: JSON.stringify({ name, notes }),
    }),

  updateProject: async (
    id: string,
    updates: Partial<Project>,
    etag?: string, // ETag for optimistic locking
  ): Promise<FullEnvelope<Project>> => {
    try {
      return await request<Project>(`/projects/${id}`, {
        method: 'PUT',
        body: JSON.stringify(updates),
        etag,
      });
    } catch (error) {
      if (error instanceof APIError && error.status === 412) {
        // ETag conflict - resource was modified
        throw new APIError(
          'Project was modified by another user. Please refresh and try again.',
          error.status,
          error.envelope,
          error.warnings,
          error.fieldErrors,
          error.etag,
        );
      }
      throw error;
    }
  },

  // Site
  resolveSite: async (
    req: SiteResolveRequest,
  ): Promise<FullEnvelope<SiteResolveResponse>> =>
    request<SiteResolveResponse>('/signage/common/site/resolve', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  // Cabinet
  deriveCabinet: async (
    req: CabinetDeriveRequest,
    cacheKey?: string,
  ): Promise<FullEnvelope<CabinetDeriveResponse>> => {
    const apiReq: CabinetDeriveRequest = {
      width_in: req.width_in,
      height_in: req.height_in,
      depth_in: req.depth_in,
      density_lb_ft3: req.density_lb_ft3,
    };
    const headers: HeadersInit = cacheKey ? { 'If-None-Match': cacheKey } : {};
    return request<CabinetDeriveResponse>('/signage/common/cabinets/derive', {
      method: 'POST',
      body: JSON.stringify(apiReq),
      headers,
    });
  },

  addCabinets: async (
    items: CabinetDeriveRequest[],
  ): Promise<FullEnvelope<CabinetDeriveResponse>> =>
    request<CabinetDeriveResponse>('/signage/common/cabinets/add', {
      method: 'POST',
      body: JSON.stringify({ items }),
    }),

  // Poles
  getPoleOptions: async (
    req: PoleOptionsRequest,
  ): Promise<FullEnvelope<Array<{ shape: string; size: string; material: string }>>> =>
    request('/signage/common/poles/options', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  // Pricing
  estimatePricing: async (
    projectId: string,
    req: PricingEstimateRequest,
  ): Promise<FullEnvelope<PricingEstimateResponse>> =>
    request<PricingEstimateResponse>(`/projects/${projectId}/estimate`, {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  // Foundation
  solveFooting: async (
    diameter_in: number,
    height_ft: number,
  ): Promise<FullEnvelope<{ volume_ft3: number; weight_lb: number }>> =>
    request('/signage/direct_burial/footing/solve', {
      method: 'POST',
      body: JSON.stringify({ diameter_in, height_ft }),
    }),

  checkBaseplate: async (
    plate_thickness_in: number,
    weld_size_in: number,
    anchors: number,
  ): Promise<FullEnvelope<{ compliant: boolean; checks: unknown[] }>> =>
    request('/signage/baseplate/checks', {
      method: 'POST',
      body: JSON.stringify({
        plate_thickness_in,
        weld_size_in,
        anchors,
      }),
    }),

  // Async Tasks
  getTaskStatus: async (taskId: string): Promise<FullEnvelope<TaskStatus>> =>
    request<TaskStatus>(`/tasks/${taskId}`),

  // File Uploads
  getPresignedUploadUrl: async (
    projectId: string,
    filename: string,
    contentType: string,
  ): Promise<FullEnvelope<FileUploadResponse>> =>
    request<FileUploadResponse>(`/projects/${projectId}/files/presign`, {
      method: 'POST',
      body: JSON.stringify({ filename, content_type: contentType }),
    }),

  attachFile: async (
    projectId: string,
    key: string,
    sha256: string,
    filename: string,
    size: number,
    contentType: string,
  ): Promise<FullEnvelope<FileAttachment>> =>
    request<FileAttachment>(`/projects/${projectId}/files/attach`, {
      method: 'POST',
      body: JSON.stringify({ key, sha256, filename, size, content_type: contentType }),
    }),

  // Project Events
  getProjectEvents: async (projectId: string): Promise<FullEnvelope<ProjectEvent[]>> =>
    request<ProjectEvent[]>(`/projects/${projectId}/events`),

  // Submission
  submitProject: async (projectId: string, idempotencyKey: string): Promise<FullEnvelope<Project>> => {
    const envelope = await request<Project>(`/projects/${projectId}/submit`, {
      method: 'POST',
      body: JSON.stringify({}), // Assuming no body needed for submit
      idempotencyKey,
    });
    // Clear idempotency key on successful submission
    localStorage.removeItem(`idempotency-${projectId}`);
    return envelope;
  },

  // Report Generation
  generateReport: async (projectId: string, idempotencyKey?: string): Promise<FullEnvelope<{ task_id: string }>> =>
    request<{ task_id: string }>(`/projects/${projectId}/report`, {
      method: 'POST',
      ...(idempotencyKey ? { idempotencyKey } : {}),
    }),

  // Export Project
  exportProject: async (projectId: string): Promise<FullEnvelope<unknown>> =>
    request<unknown>(`/projects/${projectId}/export`, {
      method: 'GET',
    }),
};
