import { useState, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { api, APIError } from '../api/client';
import { useToast } from './Toast';
import { analytics, trackEvent } from '../utils/analytics';

interface CSVRow {
  name: string;
  notes?: string;
}

interface BatchUploadProps {
  onComplete?: (projectIds: string[]) => void;
}

export default function BatchUpload({ onComplete }: BatchUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<Array<{ name: string; status: 'success' | 'error'; id?: string; error?: string }>>(
    [],
  );
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { showToast } = useToast();

  const parseCSV = (text: string): CSVRow[] => {
    const lines = text.split('\n').filter((line) => line.trim());
    if (lines.length === 0) return [];

    // Simple CSV parser (assumes first line is header)
    const headers = lines[0].split(',').map((h) => h.trim().toLowerCase());
    const nameIndex = headers.findIndex((h) => h === 'name' || h === 'project_name');
    const notesIndex = headers.findIndex((h) => h === 'notes' || h === 'description');

    if (nameIndex === -1) {
      throw new Error('CSV must contain a "name" column');
    }

    return lines.slice(1).map((line) => {
      const values = line.split(',').map((v) => v.trim());
      return {
        name: values[nameIndex] || '',
        notes: notesIndex >= 0 ? values[notesIndex] : undefined,
      };
    });
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      showToast('Please select a CSV file', 'error');
      return;
    }

    setUploading(true);
    setProgress(0);
    setResults([]);

    try {
      const text = await file.text();
      const rows = parseCSV(text);

      if (rows.length === 0) {
        throw new Error('CSV file is empty or invalid');
      }

      const resultsList: typeof results = [];
      const total = rows.length;

      // Process in parallel with concurrency limit
      const concurrency = 5;
      for (let i = 0; i < rows.length; i += concurrency) {
        const batch = rows.slice(i, i + concurrency);

        await Promise.all(
          batch.map(async (row) => {
            try {
              const response = await api.createProject(row.name, row.notes);
              // API returns FullEnvelope, check result directly
              if (response.result) {
                resultsList.push({
                  name: row.name,
                  status: 'success',
                  id: response.result.id,
                });
                analytics.projectCreated(response.result.id);
              } else {
                resultsList.push({
                  name: row.name,
                  status: 'error',
                  error: 'Failed to create project',
                });
              }
            } catch (err) {
              const message =
                err instanceof APIError ? err.message : err instanceof Error ? err.message : 'Unknown error';
              resultsList.push({
                name: row.name,
                status: 'error',
                error: message,
              });
              analytics.errorOccurred('batch_create_failed', { name: row.name });
            }
          }),
        );

        setProgress(((i + batch.length) / total) * 100);
        setResults([...resultsList]);
      }

      const successCount = resultsList.filter((r) => r.status === 'success').length;
      showToast(`Batch upload complete: ${successCount}/${total} projects created`, 'success');
      trackEvent('batch_upload_completed', {
        total: total,
        success: successCount,
      });

      if (onComplete) {
        onComplete(resultsList.filter((r) => r.id).map((r) => r.id!));
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to process CSV file';
      showToast(message, 'error');
      analytics.errorOccurred('csv_parse_failed', { error: message });
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Batch Project Creation
      </Typography>

      <Box sx={{ mt: 2 }}>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          style={{ display: 'none' }}
          onChange={handleFileSelect}
          aria-label="Upload CSV file for batch project creation"
        />
        <Button
          variant="contained"
          component="label"
          startIcon={<CloudUploadIcon />}
          disabled={uploading}
        >
          {uploading ? 'Uploading...' : 'Upload CSV'}
          <input type="file" accept=".csv" hidden onChange={handleFileSelect} />
        </Button>
      </Box>

      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
        CSV format: name,notes (optional). First row must be header.
      </Typography>

      {uploading && (
        <Box sx={{ mt: 2 }}>
          <LinearProgress variant="determinate" value={progress} />
          <Typography variant="caption" sx={{ mt: 0.5, display: 'block' }}>
            Progress: {Math.round(progress)}%
          </Typography>
        </Box>
      )}

      {results.length > 0 && (
        <TableContainer sx={{ mt: 3 }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Project Name</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Project ID</TableCell>
                <TableCell>Error</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {results.map((result, idx) => (
                <TableRow key={idx}>
                  <TableCell>{result.name}</TableCell>
                  <TableCell>
                    {result.status === 'success' ? (
                      <Typography variant="caption" color="success.main">
                        ✓ Success
                      </Typography>
                    ) : (
                      <Typography variant="caption" color="error.main">
                        ✗ Error
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                      {result.id || 'N/A'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption" color="error.main">
                      {result.error || ''}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Paper>
  );
}

