import { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Grid,
} from '@mui/material';
import { api, APIError } from '../../api/client';
import type { CabinetDeriveResponse } from '../../types/api';
import type { ResponseEnvelope } from '../../types/envelope';
import { useProjectStore } from '../../store/projectStore';
import { useToast } from '../Toast';
import { parseEnvelope } from '../../utils/envelope';
import { analytics } from '../../utils/analytics';
import ConfidenceBadge from '../ConfidenceBadge';
import EnvelopeFooter from '../EnvelopeFooter';
import InteractiveCanvas from '../InteractiveCanvas';

interface CabinetStageProps {
  projectId: string;
}

export default function CabinetStage({ projectId }: CabinetStageProps) {
  const [width, setWidth] = useState(48);
  const [height, setHeight] = useState(96);
  const [depth, setDepth] = useState(12);
  const [density, setDensity] = useState(50);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CabinetDeriveResponse | null>(null);
  const [confidence, setConfidence] = useState<number | null>(null);
  const [lastEnvelope, setLastEnvelope] = useState<ResponseEnvelope<CabinetDeriveResponse> | null>(null);
  const { updateProjectData, markStageComplete, projectData } = useProjectStore();
  const { showToast } = useToast();

  // Load saved data on mount
  useEffect(() => {
    const saved = projectData.cabinet;
    if (saved) {
      setWidth(saved.width_in || 48);
      setHeight(saved.height_in || 96);
      setDepth(saved.depth_in || 12);
      setDensity(saved.density_lb_ft3 || 50);
      if (saved.area_ft2 || saved.A_ft2) {
        setResult(saved);
      }
    }
  }, [projectData.cabinet]);

  const handleCalculate = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.deriveCabinet({
        width_in: width,
        height_in: height,
        depth_in: depth,
        density_lb_ft3: density,
      });
      
      const parsed = parseEnvelope(response);
      setConfidence(parsed.confidence);
      setLastEnvelope(response);

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
        setResult(parsed.data);
        updateProjectData('cabinet', {
          width_in: width,
          height_in: height,
          depth_in: depth,
          density_lb_ft3: density,
          ...parsed.data,
        });
        markStageComplete('cabinet');
        showToast('Cabinet calculations complete', 'success');
        analytics.stageCompleted('cabinet', projectId);
      }

      if (parsed.requiresReview) {
        showToast('Engineering review recommended', 'warning');
      }
    } catch (err) {
      const message = err instanceof APIError ? err.message : 'Failed to calculate cabinet';
      setError(message);
      showToast(message, 'error');
    } finally {
      setLoading(false);
    }
  }, [width, height, depth, density, projectId, updateProjectData, markStageComplete, showToast]);

  const isValid = width > 0 && height > 0 && depth > 0 && density > 0;

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 2 }}>
        <Box display="flex" alignItems="center" gap={2} justifyContent="space-between" mb={2}>
          <Typography variant="h5">Cabinet Design</Typography>
          {confidence !== null && <ConfidenceBadge confidence={confidence} />}
        </Box>

        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={6} sm={3}>
            <TextField
              fullWidth
              label="Width (in)"
              type="number"
              value={width}
              onChange={(e) => setWidth(Number(e.target.value))}
              error={width <= 0}
              helperText={width <= 0 ? 'Must be > 0' : ''}
            />
          </Grid>
          <Grid item xs={6} sm={3}>
            <TextField
              fullWidth
              label="Height (in)"
              type="number"
              value={height}
              onChange={(e) => setHeight(Number(e.target.value))}
              error={height <= 0}
              helperText={height <= 0 ? 'Must be > 0' : ''}
            />
          </Grid>
          <Grid item xs={6} sm={3}>
            <TextField
              fullWidth
              label="Depth (in)"
              type="number"
              value={depth}
              onChange={(e) => setDepth(Number(e.target.value))}
              error={depth <= 0}
              helperText={depth <= 0 ? 'Must be > 0' : ''}
            />
          </Grid>
          <Grid item xs={6} sm={3}>
            <TextField
              fullWidth
              label="Density (lb/ft³)"
              type="number"
              value={density}
              onChange={(e) => setDensity(Number(e.target.value))}
              error={density <= 0}
              helperText={density <= 0 ? 'Must be > 0' : ''}
            />
          </Grid>
        </Grid>

        <Button
          variant="contained"
          onClick={handleCalculate}
          disabled={loading || !isValid}
          sx={{ mt: 2 }}
        >
          {loading ? <CircularProgress size={24} /> : 'Calculate'}
        </Button>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        {result && (
          <Grid container spacing={2} sx={{ mt: 2 }}>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2">
                Area: {(result.area_ft2 || result.A_ft2 || 0).toFixed(2)} ft²
              </Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2">
                Volume: {(result.volume_ft3 || 0).toFixed(2)} ft³
              </Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2">
                Weight: {(result.weight_lb || result.weight_estimate_lb || 0).toFixed(2)} lb
              </Typography>
            </Grid>
          </Grid>
        )}
      </Paper>

      <InteractiveCanvas />

      <EnvelopeFooter envelope={lastEnvelope} />
    </Box>
  );
}