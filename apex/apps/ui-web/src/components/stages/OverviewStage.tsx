import { useState, useEffect, useCallback } from 'react';
import { Box, Paper, Typography, CircularProgress, Alert, Button } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import { api } from '../../api/client';
import { useProjectStore } from '../../store/projectStore';
import ExportDialog from '../ExportDialog';
import type { Project } from '../../types/api';

interface OverviewStageProps {
  projectId: string;
}

export default function OverviewStage({ projectId }: OverviewStageProps) {
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const { markStageComplete } = useProjectStore();

  const loadProject = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.getProject(projectId);
      if (response.result) {
        setProject(response.result);
      }
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load project');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadProject();
    markStageComplete('overview');
  }, [projectId, loadProject, markStageComplete]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Project Overview
      </Typography>
      {project && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body1" gutterBottom>
            <strong>Name:</strong> {project.name}
          </Typography>
          <Typography variant="body1" gutterBottom>
            <strong>Status:</strong> {project.status}
          </Typography>
          {project.notes && (
            <Typography variant="body1" gutterBottom>
              <strong>Notes:</strong> {project.notes}
            </Typography>
          )}
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Created: {new Date(project.created_at).toLocaleString()}
          </Typography>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={() => setExportDialogOpen(true)}
            sx={{ mt: 2 }}
            aria-label="Export project data"
          >
            Export Project
          </Button>
        </Box>
      )}
      <ExportDialog
        open={exportDialogOpen}
        onClose={() => setExportDialogOpen(false)}
        projectId={projectId}
      />
    </Paper>
  );
}
