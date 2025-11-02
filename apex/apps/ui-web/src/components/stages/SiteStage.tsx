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
import { useProjectStore } from '../../store/projectStore';
import { useToast } from '../Toast';
import { parseEnvelope } from '../../utils/envelope';
import ConfidenceBadge from '../ConfidenceBadge';
import type { SiteResolveResponse } from '../../types/api';

interface SiteStageProps {
  projectId: string;
}

export default function SiteStage({ projectId: _projectId }: SiteStageProps) {
  const [address, setAddress] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SiteResolveResponse | null>(null);
  const [confidence, setConfidence] = useState<number | null>(null);
  const { updateProjectData, markStageComplete, projectData } = useProjectStore();
  const { showToast } = useToast();

  // Load saved data on mount
  useEffect(() => {
    const saved = projectData.site;
    if (saved) {
      setAddress(saved.address || '');
      if (saved.latitude && saved.longitude) {
        setResult(saved);
      }
      return;
    }
  }, [projectData.site]);

  const handleResolve = useCallback(async () => {
    if (!address.trim()) return;

    try {
      setLoading(true);
      setError(null);
      const response = await api.resolveSite({ address: address.trim() });
      const parsed = parseEnvelope(response);
      setConfidence(parsed.confidence);

      // Show warnings
      if (parsed.warnings.length > 0) {
        parsed.warnings.forEach((w) => showToast(`Warning: ${w}`, 'warning'));
      }

      if (parsed.data) {
        setResult(parsed.data);
        updateProjectData('site', {
          address: address.trim(),
          ...parsed.data,
        });
        markStageComplete('site');
        showToast('Site resolved successfully', 'success');
      }

      if (parsed.requiresReview) {
        showToast('Engineering review recommended', 'warning');
      }
    } catch (err) {
      const message =
        err instanceof APIError ? err.message : err instanceof Error ? err.message : 'Failed to resolve site';
      setError(message);
      showToast(message, 'error');
    } finally {
      setLoading(false);
    }
  }, [address, updateProjectData, markStageComplete, showToast]);

  return (
    <Paper sx={{ p: 3 }}>
      <Box display="flex" alignItems="center" gap={2} justifyContent="space-between" mb={2}>
        <Typography variant="h5">Site & Environmental Data</Typography>
        {confidence !== null && <ConfidenceBadge confidence={confidence} />}
      </Box>

      <Box sx={{ mt: 3 }}>
        <TextField
          fullWidth
          label="Address"
          placeholder="123 Main St, City, State ZIP"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleResolve()}
        />
        <Button
          variant="contained"
          onClick={handleResolve}
          disabled={!address.trim() || loading}
          sx={{ mt: 2 }}
        >
          {loading ? <CircularProgress size={24} /> : 'Resolve Location'}
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      {result && (
        <Grid container spacing={2} sx={{ mt: 2 }}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" gutterBottom>
              Location
            </Typography>
            <Typography variant="body2">
              Latitude: {result.latitude?.toFixed(6) || result.lat?.toFixed(6) || 'N/A'}
            </Typography>
            <Typography variant="body2">
              Longitude: {result.longitude?.toFixed(6) || result.lon?.toFixed(6) || 'N/A'}
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" gutterBottom>
              Wind Data
            </Typography>
            <Typography variant="body2">
              Wind Speed: {result.wind_speed_mph || 'N/A'} mph
            </Typography>
            <Typography variant="body2">
              Exposure: {result.exposure || 'N/A'}
            </Typography>
            {(result.snow_load_psf || result.snow_load_psf === 0) && (
              <Typography variant="body2">
                Snow Load: {result.snow_load_psf} psf
              </Typography>
            )}
          </Grid>
        </Grid>
      )}
    </Paper>
  );
}