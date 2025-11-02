/**
 * Analytics tracking utilities
 * Supports Google Analytics (gtag) and custom event logging
 */

declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void;
    plausible?: (event: string, options?: { props?: Record<string, unknown> }) => void;
    Sentry?: {
      addBreadcrumb: (breadcrumb: {
        category: string;
        message: string;
        data?: Record<string, unknown>;
        level: string;
      }) => void;
    };
  }
}

export function trackEvent(
  eventName: string,
  properties?: Record<string, unknown>,
): void {
  // Google Analytics
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', eventName, properties);
  }

  // Plausible Analytics
  if (typeof window !== 'undefined' && window.plausible) {
    window.plausible(eventName, { props: properties });
  }

  // Sentry breadcrumb
  if (typeof window !== 'undefined' && window.Sentry) {
    window.Sentry.addBreadcrumb({
      category: 'user',
      message: eventName,
      data: properties,
      level: 'info',
    });
  }

  // Console in development
  if (import.meta.env.DEV) {
    console.log('[Analytics]', eventName, properties);
  }
}

// Predefined event trackers
export const analytics = {
  projectCreated: (projectId: string) =>
    trackEvent('project_created', { project_id: projectId }),

  stageCompleted: (stage: string, projectId: string) =>
    trackEvent('stage_completed', { stage, project_id: projectId }),

  submissionCompleted: (projectId: string, confidence: number) =>
    trackEvent('submission_completed', { project_id: projectId, confidence }),

  deriveUsed: (projectId: string, dimensions: { width: number; height: number }) =>
    trackEvent('derive_used', { project_id: projectId, ...dimensions }),

  fileUploaded: (projectId: string, fileType: string, size: number) =>
    trackEvent('file_uploaded', { project_id: projectId, file_type: fileType, size }),

  lowConfidenceWarning: (stage: string, confidence: number) =>
    trackEvent('low_confidence_warning', { stage, confidence }),

  errorOccurred: (error: string, context?: Record<string, unknown>) =>
    trackEvent('error_occurred', { error, ...context }),
};
