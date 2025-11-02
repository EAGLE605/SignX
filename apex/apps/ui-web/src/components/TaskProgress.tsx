import { Box, Paper, Typography, LinearProgress, Alert, CircularProgress } from '@mui/material';
import { useTaskPolling } from '../hooks/useTaskPolling';

interface TaskProgressProps {
  taskId: string | null;
  onComplete?: (result: unknown) => void;
  onError?: (error: string) => void;
  title?: string;
}

export default function TaskProgress({ taskId, title = 'Processing task', onComplete, onError }: TaskProgressProps) {
  const { status, isPolling } = useTaskPolling({
    taskId: taskId || null,
    onComplete,
    onError,
  });

  if (!taskId || (!isPolling && !status)) {
    return null;
  }

  const getStatusLabel = () => {
    if (!status) return 'Initializing...';
    switch (status.status) {
      case 'pending':
        return 'Queued';
      case 'processing':
        return 'Processing...';
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      default:
        return 'Unknown';
    }
  };

  return (
    <Paper sx={{ p: 3, mb: 2 }}>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>

      <Box sx={{ mt: 2 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
          <Typography variant="body2" color="text.secondary">
            {getStatusLabel()}
          </Typography>
          {status?.progress !== undefined && (
            <Typography variant="body2" color="text.secondary">
              {status.progress}%
            </Typography>
          )}
        </Box>

        {(status?.status === 'processing' || status?.status === 'pending') && (
          <LinearProgress
            variant={status?.progress !== undefined ? 'determinate' : 'indeterminate'}
            value={status?.progress || 0}
            sx={{ mb: 2 }}
          />
        )}

        {status?.status === 'completed' && (
          <Alert severity="success" sx={{ mt: 2 }}>
            Task completed successfully!
          </Alert>
        )}

        {status?.status === 'failed' && status.error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {status.error}
          </Alert>
        )}

        {status?.status === 'processing' && (
          <Box display="flex" alignItems="center" gap={1} mt={1}>
            <CircularProgress size={16} />
            <Typography variant="caption" color="text.secondary">
              Please wait...
            </Typography>
          </Box>
        )}
      </Box>
    </Paper>
  );
}
