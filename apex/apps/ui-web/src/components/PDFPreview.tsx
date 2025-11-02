import { useState, useEffect, useCallback, memo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Alert,
  CircularProgress,
  IconButton,
} from '@mui/material';
import GetAppIcon from '@mui/icons-material/GetApp';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';

interface PDFPreviewProps {
  projectId: string;
  pdfUrl?: string;
}

function PDFPreviewComponent({ projectId, pdfUrl }: PDFPreviewProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pdfData, setPdfData] = useState<string | null>(null);

  const loadPDF = useCallback(async () => {
    if (!pdfUrl) return;

    try {
      setLoading(true);
      setError(null);
      // In production, this would fetch the actual PDF
      // For now, we'll use a placeholder
      setPdfData(pdfUrl);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load PDF');
    } finally {
      setLoading(false);
    }
  }, [pdfUrl]);

  useEffect(() => {
    if (pdfUrl) {
      loadPDF();
    }
  }, [pdfUrl, loadPDF]);

  const handleDownload = () => {
    if (pdfData) {
      const link = document.createElement('a');
      link.href = pdfData;
      link.download = `project-${projectId}-report.pdf`;
      link.click();
    }
  };

  const handleOpenInNewTab = () => {
    if (pdfData) {
      window.open(pdfData, '_blank');
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">PDF Report Preview</Typography>
        {pdfData && (
          <Box>
            <IconButton onClick={handleOpenInNewTab} title="Open in new tab">
              <OpenInNewIcon />
            </IconButton>
            <IconButton onClick={handleDownload} title="Download">
              <GetAppIcon />
            </IconButton>
          </Box>
        )}
      </Box>

      {loading && (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      )}

      {error && <Alert severity="error">{error}</Alert>}

      {pdfData && !loading && (
        <Box
          component="iframe"
          src={pdfData}
          sx={{
            width: '100%',
            height: '600px',
            border: '1px solid #ddd',
            borderRadius: 1,
          }}
          title="PDF Preview"
        />
      )}

      {!pdfData && !loading && !error && (
        <Alert severity="info">No PDF available. Generate a report to preview.</Alert>
      )}
    </Paper>
  );
}

export default memo(PDFPreviewComponent);