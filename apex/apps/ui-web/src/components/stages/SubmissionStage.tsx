import { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material';
import { useProjectStore } from '../../store/projectStore';
import { validateStage } from '../../utils/validation';
import { useToast } from '../Toast';
import { api, APIError } from '../../api/client';
import { parseEnvelope } from '../../utils/envelope';
import {
  generateIdempotencyKey,
  getStoredIdempotencyKey,
  storeIdempotencyKey,
  clearIdempotencyKey,
} from '../../utils/envelope';
import ConfidenceBadge from '../ConfidenceBadge';

interface SubmissionStageProps {
  projectId: string;
}

export default function SubmissionStage({ projectId }: SubmissionStageProps) {
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [overallConfidence, setOverallConfidence] = useState<number | null>(null);
  const { markStageComplete, projectData } = useProjectStore();
  const { showToast } = useToast();

  // Calculate overall confidence from all stages
  useEffect(() => {
    // In production, this would aggregate confidence from all API calls
    // For now, use a simple average or minimum
    const confidences: number[] = [];
    // Assume each stage has a confidence if completed
    if (projectData.site) confidences.push(0.9);
    if (projectData.cabinet) confidences.push(0.95);
    if (projectData.structural) confidences.push(0.85);
    if (projectData.foundation) confidences.push(0.8);
    if (projectData.pricing) confidences.push(1.0); // Deterministic

    if (confidences.length > 0) {
      setOverallConfidence(Math.min(...confidences)); // Use minimum for conservative estimate
    }
  }, [projectData]);

  const handleSubmit = useCallback(async () => {
    // Validate all required stages
    const requiredStages: Array<'site' | 'cabinet' | 'structural' | 'foundation' | 'finalization'> = [
      'site',
      'cabinet',
      'structural',
      'foundation',
      'finalization',
    ];

    const validationErrors: string[] = [];
    for (const stage of requiredStages) {
      const validation = validateStage(stage, projectData);
      if (!validation.isValid) {
        validationErrors.push(...validation.errors.map((e) => `${stage}: ${e}`));
      }
    }

    if (validationErrors.length > 0) {
      setError(`Validation errors:\n${validationErrors.join('\n')}`);
      showToast('Please complete all required stages', 'warning');
      return;
    }

    // Get or generate idempotency key
    let idempotencyKey = getStoredIdempotencyKey(projectId);
    if (!idempotencyKey) {
      idempotencyKey = generateIdempotencyKey();
      storeIdempotencyKey(projectId, idempotencyKey);
    }

    try {
      setSubmitting(true);
      setError(null);

      const response = await api.submitProject(projectId, idempotencyKey);
      const parsed = parseEnvelope(response);

      // Show warnings
      if (parsed.warnings.length > 0) {
        parsed.warnings.forEach((w) => showToast(`Warning: ${w}`, 'warning'));
      }

      // Show field errors
      if (parsed.errors.length > 0) {
        parsed.errors.forEach((err) => {
          showToast(`Validation error: ${err.field}: ${err.message}`, 'error');
        });
      }

      if (parsed.data) {
        setSubmitted(true);
        markStageComplete('submission');
        clearIdempotencyKey(projectId); // Clear on success
        showToast('Project submitted successfully', 'success');
        const { analytics } = await import('../../utils/analytics');
        analytics.submissionCompleted(projectId, parsed.confidence);
      } else if (parsed.requiresReview) {
        setError('Submission requires engineering review due to low confidence');
        showToast('Engineering review required', 'warning');
      }
    } catch (err) {
      // Retry with same idempotency key on network failure
      const message =
        err instanceof APIError ? err.message : err instanceof Error ? err.message : 'Submission failed';
      setError(message);
      showToast(message, 'error');

      // Keep idempotency key for retry
    } finally {
      setSubmitting(false);
      setConfirmOpen(false);
    }
  }, [projectId, projectData, markStageComplete, showToast]);

  return (
    <>
      <Paper sx={{ p: 3 }}>
        <Box display="flex" alignItems="center" gap={2} justifyContent="space-between" mb={2}>
          <Typography variant="h5" gutterBottom>
            Submit Project
          </Typography>
          {overallConfidence !== null && <ConfidenceBadge confidence={overallConfidence} />}
        </Box>

        {submitted ? (
          <Alert severity="success" sx={{ mt: 2 }}>
            Project submitted successfully! You will receive a confirmation email shortly.
          </Alert>
        ) : (
          <>
            <Typography variant="body1" sx={{ mt: 2 }}>
              Submit your project for engineering review and approval. All required stages must be
              completed.
            </Typography>

            {overallConfidence !== null && overallConfidence < 0.5 && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                Overall confidence is low ({Math.round(overallConfidence * 100)}%). Engineering review
                is strongly recommended before submission.
              </Alert>
            )}

            <Button
              variant="contained"
              onClick={() => setConfirmOpen(true)}
              disabled={submitting}
              sx={{ mt: 2 }}
            >
              {submitting ? <CircularProgress size={24} /> : 'Submit Project'}
            </Button>

            {error && (
              <Alert severity="error" sx={{ mt: 2, whiteSpace: 'pre-line' }}>
                {error}
              </Alert>
            )}
          </>
        )}
      </Paper>

      <Dialog open={confirmOpen} onClose={() => setConfirmOpen(false)}>
        <DialogTitle>Confirm Submission</DialogTitle>
        <DialogContent>
          <DialogContentText>
            {overallConfidence !== null && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Overall Confidence: {Math.round(overallConfidence * 100)}%
                </Typography>
                <ConfidenceBadge confidence={overallConfidence} showLabel={false} />
              </Box>
            )}
            Are you sure you want to submit this project? All data will be locked for review.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmOpen(false)}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained" disabled={submitting}>
            {submitting ? <CircularProgress size={20} /> : 'Confirm Submit'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}