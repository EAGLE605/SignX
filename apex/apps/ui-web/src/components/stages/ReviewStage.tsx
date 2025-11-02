import { useState, useEffect } from 'react';
import { Box, Paper, Typography, Button, Alert } from '@mui/material';
import { useProjectStore } from '../../store/projectStore';
import { validateStage } from '../../utils/validation';
import PDFPreview from '../PDFPreview';
import TaskProgress from '../TaskProgress';
import EnvelopeFooter from '../EnvelopeFooter';
import ProjectHistory from '../ProjectHistory';
import { api, APIError } from '../../api/client';
import { useToast } from '../Toast';
import { parseEnvelope } from '../../utils/envelope';
import type { ResponseEnvelope } from '../../types/envelope';

interface ReviewStageProps {
  projectId: string;
}

export default function ReviewStage({ projectId }: ReviewStageProps) {
  const { projectData, markStageComplete } = useProjectStore();
  const [reportTaskId, setReportTaskId] = useState<string | null>(null);
  const [lastEnvelope, setLastEnvelope] = useState<ResponseEnvelope<unknown> | null>(null);
  const { showToast } = useToast();

  const handleComplete = () => {
    markStageComplete('review');
    showToast('Review stage marked complete', 'success');
  };

  const handleGenerateReport = async () => {
    try {
      const response = await api.generateReport(projectId);
      const parsed = parseEnvelope(response);
      if (parsed.data?.task_id) {
        setReportTaskId(parsed.data.task_id);
        showToast('Report generation started', 'info');
      }
    } catch (error) {
      const message =
        error instanceof APIError ? error.message : error instanceof Error ? error.message : 'Failed to generate report';
      showToast(message, 'error');
    }
  };

  // Load project events
  useEffect(() => {
    const loadEvents = async () => {
      try {
        const response = await api.getProjectEvents(projectId);
        const parsed = parseEnvelope(response);
        if (parsed.data) {
          setLastEnvelope(response);
        }
      } catch (error) {
        // Silently fail - events are optional
      }
    };
    loadEvents();
  }, [projectId]);

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 2 }}>
        <Typography variant="h5" gutterBottom>
          Review & Validation
        </Typography>

        <Typography variant="body1" sx={{ mt: 2 }}>
          Review all project data before submission:
        </Typography>

        <Box sx={{ mt: 2 }}>
          {['site', 'cabinet', 'structural', 'foundation', 'finalization'].map((stage) => {
            const validation = validateStage(stage as any, projectData);
            return validation.isValid ? (
              <Alert key={stage} severity="success" sx={{ mb: 1 }}>
                {stage.charAt(0).toUpperCase() + stage.slice(1)} stage complete
              </Alert>
            ) : (
              <Alert key={stage} severity="warning" sx={{ mb: 1 }}>
                {stage.charAt(0).toUpperCase() + stage.slice(1)}: {validation.errors.join(', ')}
              </Alert>
            );
          })}
        </Box>

        <Button variant="contained" onClick={handleComplete} sx={{ mt: 2 }}>
          Mark Review Complete
        </Button>

        <Button variant="outlined" onClick={handleGenerateReport} sx={{ mt: 2, ml: 2 }}>
          Generate Report
        </Button>
      </Paper>

      {reportTaskId && (
        <TaskProgress
          taskId={reportTaskId}
          title="Generating Report"
          onComplete={(result: unknown) => {
            if (result && typeof result === 'object' && 'pdf_url' in result) {
              window.open((result as { pdf_url: string }).pdf_url, '_blank');
              showToast('Report generated successfully', 'success');
            }
          }}
          onError={(error) => {
            showToast(`Report generation failed: ${error}`, 'error');
          }}
        />
      )}

      <PDFPreview projectId={projectId} />

      <ProjectHistory projectId={projectId} />

      <EnvelopeFooter envelope={lastEnvelope} />
    </Box>
  );
}