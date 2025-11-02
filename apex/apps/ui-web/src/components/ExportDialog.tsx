import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  RadioGroup,
  FormControlLabel,
  Radio,
  Typography,
} from '@mui/material';
import { api } from '../api/client';
import { useToast } from './Toast';
import { analytics, trackEvent } from '../utils/analytics';

interface ExportDialogProps {
  open: boolean;
  onClose: () => void;
  projectId: string;
}

export default function ExportDialog({ open, onClose, projectId }: ExportDialogProps) {
  const [format, setFormat] = useState<'json' | 'pdf'>('json');
  const [exporting, setExporting] = useState(false);
  const { showToast } = useToast();

  const handleExport = async () => {
    try {
      setExporting(true);

      if (format === 'json') {
        const response = await api.exportProject(projectId);
        const parsed = parseEnvelope(response);
        if (parsed.data) {
          const blob = new Blob([JSON.stringify(parsed.data, null, 2)], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `project-${projectId}-export.json`;
          link.click();
          URL.revokeObjectURL(url);
          showToast('Project exported as JSON', 'success');
          trackEvent('project_exported', { format: 'json', project_id: projectId });
        }
      } else {
        // PDF export via report generation
        const response = await api.generateReport(projectId);
        const parsed = parseEnvelope(response);
        if (parsed.data?.task_id) {
          showToast('PDF generation started. Check Review stage for progress.', 'info');
          trackEvent('project_exported', { format: 'pdf', project_id: projectId });
        }
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Export failed';
      showToast(message, 'error');
      analytics.errorOccurred('export_failed', { format, project_id: projectId });
    } finally {
      setExporting(false);
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={onClose} aria-labelledby="export-dialog-title">
      <DialogTitle id="export-dialog-title">Export Project</DialogTitle>
      <DialogContent>
        <Typography variant="body2" gutterBottom>
          Choose export format:
        </Typography>
        <RadioGroup value={format} onChange={(e) => setFormat(e.target.value as 'json' | 'pdf')}>
          <FormControlLabel
            value="json"
            control={<Radio />}
            label="JSON (includes full envelope metadata)"
          />
          <FormControlLabel value="pdf" control={<Radio />} label="PDF Report" />
        </RadioGroup>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleExport} variant="contained" disabled={exporting}>
          {exporting ? 'Exporting...' : 'Export'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

import { parseEnvelope } from '../utils/envelope';
