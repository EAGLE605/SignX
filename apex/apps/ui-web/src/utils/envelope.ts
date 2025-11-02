/**
 * Envelope parsing and utility functions
 */

import type { ResponseEnvelope, ConfidenceLevel } from '../types/envelope';

export interface ParsedEnvelope<T> {
  data: T | null;
  warnings: string[];
  errors: Array<{ field: string; message: string }>;
  confidence: number;
  confidenceLevel: ConfidenceLevel;
  traceId?: string;
  constantsVersion?: string;
  contentSha256?: string;
  requiresReview: boolean;
}

export function parseEnvelope<T>(envelope: ResponseEnvelope<T>): ParsedEnvelope<T> {
  const warnings = envelope.warnings || [];
  const errors = envelope.errors || [];
  const confidence = envelope.confidence ?? 1.0;
  const requiresReview = confidence < 0.5;

  return {
    data: envelope.result,
    warnings,
    errors,
    confidence,
    confidenceLevel: getConfidenceLevel(confidence),
    traceId: envelope.trace?.code_version?.git_sha,
    constantsVersion: envelope.trace?.constants_version,
    contentSha256: envelope.content_sha256,
    requiresReview,
  };
}

export function getConfidenceLevel(confidence: number): ConfidenceLevel {
  if (confidence >= 0.9) return 'high';
  if (confidence >= 0.7) return 'medium';
  return 'low';
}

export function generateIdempotencyKey(): string {
  return `idempotency-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

export function getStoredIdempotencyKey(projectId: string): string | null {
  try {
    return localStorage.getItem(`idempotency-${projectId}`) || null;
  } catch {
    return null;
  }
}

export function storeIdempotencyKey(projectId: string, key: string): void {
  try {
    localStorage.setItem(`idempotency-${projectId}`, key);
  } catch {
    // Ignore storage errors
  }
}

export function clearIdempotencyKey(projectId: string): void {
  try {
    localStorage.removeItem(`idempotency-${projectId}`);
  } catch {
    // Ignore storage errors
  }
}
