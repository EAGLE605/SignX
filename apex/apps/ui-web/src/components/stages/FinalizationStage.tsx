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
  Checkbox,
  FormControlLabel,
} from '@mui/material';
import { api, APIError } from '../../api/client';
import { useProjectStore } from '../../store/projectStore';
import { useToast } from '../Toast';
import { parseEnvelope } from '../../utils/envelope';
import ConfidenceBadge from '../ConfidenceBadge';
import type { PricingEstimateResponse } from '../../types/api';

interface FinalizationStageProps {
  projectId: string;
}

export default function FinalizationStage({ projectId }: FinalizationStageProps) {
  const [height, setHeight] = useState(20);
  const [addons, setAddons] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pricing, setPricing] = useState<PricingEstimateResponse | null>(null);
  const [confidence, setConfidence] = useState<number | null>(null);
  const { updateProjectData, markStageComplete, projectData } = useProjectStore();
  const { showToast } = useToast();

  // Load saved data on mount
  useEffect(() => {
    const saved = projectData.pricing;
    if (saved) {
      setHeight(saved.height_ft || 20);
      setAddons(saved.addons || []);
      if (saved.total) {
        setPricing(saved);
      }
    }
  }, [projectData.pricing]);

  const handleEstimate = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.estimatePricing(projectId, {
        height_ft: height,
        addons,
      });
      const parsed = parseEnvelope(response);
      setConfidence(parsed.confidence);

      // Show warnings
      if (parsed.warnings.length > 0) {
        parsed.warnings.forEach((w) => showToast(`Warning: ${w}`, 'warning'));
      }

      if (parsed.data) {
        setPricing(parsed.data);
        updateProjectData('pricing', parsed.data);
        markStageComplete('finalization');
        showToast('Pricing estimate calculated', 'success');
      }

      if (parsed.requiresReview) {
        showToast('Engineering review recommended', 'warning');
      }
    } catch (err) {
      const message =
        err instanceof APIError
          ? err.message
          : err instanceof Error
          ? err.message
          : 'Failed to estimate pricing';
      setError(message);
      showToast(message, 'error');
    } finally {
      setLoading(false);
    }
  }, [height, addons, projectId, updateProjectData, markStageComplete, showToast]);

  const handleAddonToggle = (addon: string) => {
    setAddons((prev) => (prev.includes(addon) ? prev.filter((a) => a !== addon) : [...prev, addon]));
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Box display="flex" alignItems="center" gap={2} justifyContent="space-between" mb={2}>
        <Typography variant="h5">Finalization & Pricing</Typography>
        {confidence !== null && <ConfidenceBadge confidence={confidence} />}
      </Box>

      <Grid container spacing={2} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Height (ft)"
            type="number"
            value={height}
            onChange={(e) => setHeight(Number(e.target.value))}
            error={height <= 0}
            helperText={height <= 0 ? 'Must be > 0' : ''}
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <Typography variant="subtitle2" gutterBottom>
            Add-on Services
          </Typography>
          <FormControlLabel
            control={
              <Checkbox
                checked={addons.includes('calc_packet')}
                onChange={() => handleAddonToggle('calc_packet')}
              />
            }
            label="Calculation Packet"
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={addons.includes('hard_copies')}
                onChange={() => handleAddonToggle('hard_copies')}
              />
            }
            label="Hard Copies"
          />
        </Grid>
      </Grid>

      <Button
        variant="contained"
        onClick={handleEstimate}
        disabled={loading || height <= 0}
        sx={{ mt: 2 }}
      >
        {loading ? <CircularProgress size={24} /> : 'Get Estimate'}
      </Button>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      {pricing && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Pricing Estimate
          </Typography>
          {pricing.items?.map((item: any, idx: number) => (
            <Typography key={idx} variant="body2">
              {item.item}: ${item.price?.toFixed(2) || '0.00'}
            </Typography>
          ))}
          <Typography variant="h6" sx={{ mt: 2 }}>
            Total: ${pricing.total?.toFixed(2) || '0.00'}
          </Typography>
        </Box>
      )}
    </Paper>
  );
}