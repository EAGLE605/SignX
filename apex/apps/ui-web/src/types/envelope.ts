/**
 * Extended Envelope types with all APEX fields
 */

export interface ResponseEnvelope<T = unknown> {
  result: T | null;
  assumptions: string[];
  warnings?: string[];
  errors?: Array<{ field: string; message: string }>;
  confidence: number;
  content_sha256?: string;
  trace: {
    data: {
      inputs: Record<string, unknown>;
      intermediates: Record<string, unknown>;
      outputs: Record<string, unknown>;
    };
    code_version: {
      git_sha: string;
      dirty: boolean;
      build_id?: string;
    };
    constants_version?: string;
    model_config: {
      provider: string;
      model: string;
      temperature: number;
      max_tokens: number;
      seed?: number | null;
    };
  };
}

export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  result?: unknown;
  error?: string;
}

export interface FileUploadResponse {
  url: string;
  key: string;
  expires_in: number;
}

export interface FileAttachment {
  key: string;
  sha256: string;
  filename: string;
  size: number;
  content_type: string;
  uploaded_at: string;
}

export interface ProjectEvent {
  id: string;
  project_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export type ConfidenceLevel = 'high' | 'medium' | 'low';

export function getConfidenceLevel(confidence: number): ConfidenceLevel {
  if (confidence >= 0.9) return 'high';
  if (confidence >= 0.7) return 'medium';
  return 'low';
}

export function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.9) return '#4caf50'; // green
  if (confidence >= 0.7) return '#ff9800'; // orange
  return '#f44336'; // red
}
