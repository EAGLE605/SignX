import { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  TextField,
  Typography,
  Alert,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import AddIcon from '@mui/icons-material/Add';
import { api, APIError } from '../api/client';
import type { Project } from '../types/api';
import { useProjectStore } from '../store/projectStore';
import { useToast } from './Toast';
import { analytics } from '../utils/analytics';
import BatchUpload from './BatchUpload';

export default function ProjectList() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectNotes, setNewProjectNotes] = useState('');
  const [creating, setCreating] = useState(false);
  const [batchDialogOpen, setBatchDialogOpen] = useState(false);
  const { setCurrentProject } = useProjectStore();
  const { showToast } = useToast();

  const loadProjects = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.listProjects();
      if (response.result) {
        setProjects(response.result);
      }
      setError(null);
    } catch (err) {
      const message =
        err instanceof APIError ? err.message : err instanceof Error ? err.message : 'Failed to load projects';
      setError(message);
      showToast(message, 'error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;

    try {
      setCreating(true);
      // Optimistic update
      const optimisticProject: Project = {
        id: `temp-${Date.now()}`,
        name: newProjectName.trim(),
        notes: newProjectNotes.trim() || undefined,
        status: 'draft',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setProjects([optimisticProject, ...projects]);

      const response = await api.createProject(newProjectName.trim(), newProjectNotes.trim() || undefined);
      if (response.result) {
        // Replace optimistic with real project
        setProjects((prev) => [response.result!, ...prev.filter((p) => p.id !== optimisticProject.id)]);
        setDialogOpen(false);
        setNewProjectName('');
        setNewProjectNotes('');
        showToast('Project created successfully', 'success');
        analytics.projectCreated(response.result.id);
        navigate(`/projects/${response.result.id}`);
      }
    } catch (err) {
      // Rollback optimistic update
      setProjects((prev) => prev.filter((p) => !p.id.startsWith('temp-')));
      const message =
        err instanceof APIError ? err.message : err instanceof Error ? err.message : 'Failed to create project';
      setError(message);
      showToast(message, 'error');
    } finally {
      setCreating(false);
    }
  };

  const handleSelectProject = (project: Project) => {
    setCurrentProject(project.id);
    navigate(`/projects/${project.id}`);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4} flexWrap="wrap" gap={2}>
        <Typography variant="h4" component="h1">
          Projects
        </Typography>
        <Box display="flex" gap={1}>
          <Button
            variant="outlined"
            onClick={() => setBatchDialogOpen(true)}
            aria-label="Batch upload projects from CSV"
          >
            Batch Upload
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setDialogOpen(true)}
            aria-label="Create new project"
          >
            New Project
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {projects.length === 0 ? (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="body1" color="text.secondary" align="center">
                  No projects yet. Create your first project to get started.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ) : (
          projects.map((project) => (
            <Grid item xs={12} sm={6} md={4} key={project.id}>
              <Card
                sx={{ cursor: 'pointer', height: '100%' }}
                onClick={() => handleSelectProject(project)}
              >
                <CardContent>
                  <Typography variant="h6" component="h2" gutterBottom>
                    {project.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Status: {project.status}
                  </Typography>
                  {project.notes && (
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      {project.notes}
                    </Typography>
                  )}
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
                    Created: {new Date(project.created_at).toLocaleDateString()}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))
        )}
      </Grid>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Project</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <TextField
            autoFocus
            margin="dense"
            label="Project Name"
            fullWidth
            variant="outlined"
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
            required
          />
          <TextField
            margin="dense"
            label="Notes (Optional)"
            fullWidth
            variant="outlined"
            multiline
            rows={3}
            value={newProjectNotes}
            onChange={(e) => setNewProjectNotes(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateProject}
            variant="contained"
            disabled={!newProjectName.trim() || creating}
          >
            {creating ? <CircularProgress size={20} /> : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={batchDialogOpen}
        onClose={() => setBatchDialogOpen(false)}
        maxWidth="md"
        fullWidth
        aria-labelledby="batch-upload-dialog-title"
      >
        <DialogTitle id="batch-upload-dialog-title">Batch Upload Projects</DialogTitle>
        <DialogContent>
          <BatchUpload
            onComplete={() => {
              setBatchDialogOpen(false);
              loadProjects(); // Reload to show new projects
            }}
          />
        </DialogContent>
      </Dialog>
    </Box>
  );
}
