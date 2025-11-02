import { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import { api, APIError } from '../../api/client';
import { useProjectStore } from '../../store/projectStore';
import { useToast } from '../Toast';
import { parseEnvelope } from '../../utils/envelope';
import type { PoleOption } from '../../types/api';
import ConfidenceBadge from '../ConfidenceBadge';

interface StructuralStageProps {
  projectId: string;
}

export default function StructuralStage({ projectId: _projectId }: StructuralStageProps) {
  const [momentRequired, setMomentRequired] = useState(2500);
  const [material, setMaterial] = useState<'steel' | 'aluminum'>('steel');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [options, setOptions] = useState<PoleOption[]>([]);
  const [confidence, setConfidence] = useState<number | null>(null);
  const { updateProjectData, markStageComplete, projectData } = useProjectStore();
  const { showToast } = useToast();

  // Load saved data on mount
  useEffect(() => {
    const saved = projectData.structural;
    if (saved) {
      setMomentRequired(saved.moment_required_ft_lb || 2500);
      if ('material' in saved) {
        setMaterial(saved.material as 'steel' | 'aluminum');
      }
      if ('options' in saved && Array.isArray(saved.options)) {
        setOptions(saved.options as PoleOption[]);
      }
    }
  }, [projectData.structural]);

  const handleSearch = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.getPoleOptions({
        moment_required_ft_lb: momentRequired,
        material,
      });
      const parsed = parseEnvelope(response);
      setConfidence(parsed.confidence);

      // Show warnings
      if (parsed.warnings.length > 0) {
        parsed.warnings.forEach((w) => showToast(`Warning: ${w}`, 'warning'));
      }

      if (parsed.data) {
        const poleOptions = Array.isArray(parsed.data) ? parsed.data : (parsed.data as any).options || [];
        setOptions(poleOptions);
        updateProjectData('structural', {
          moment_required_ft_lb: momentRequired,
          material,
          options: poleOptions,
        });
        if (poleOptions.length > 0) {
          markStageComplete('structural');
          showToast(`${poleOptions.length} pole options found`, 'success');
        }
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
          : 'Failed to fetch pole options';
      setError(message);
      showToast(message, 'error');
    } finally {
      setLoading(false);
    }
  }, [momentRequired, material, updateProjectData, markStageComplete, showToast]);

  return (
    <Paper sx={{ p: 3 }}>
      <Box display="flex" alignItems="center" gap={2} justifyContent="space-between" mb={2}>
        <Typography variant="h5">Structural Design - Pole Selection</Typography>
        {confidence !== null && <ConfidenceBadge confidence={confidence} />}
      </Box>

      <Box sx={{ mt: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <TextField
          label="Moment Required (ft-lb)"
          type="number"
          value={momentRequired}
          onChange={(e) => setMomentRequired(Number(e.target.value))}
          error={momentRequired <= 0}
          helperText={momentRequired <= 0 ? 'Must be > 0' : ''}
        />
        <Button variant="contained" onClick={handleSearch} disabled={loading || momentRequired <= 0}>
          {loading ? <CircularProgress size={24} /> : 'Search Options'}
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      {options.length > 0 && (
        <TableContainer sx={{ mt: 3 }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Shape</TableCell>
                <TableCell>Size</TableCell>
                <TableCell>Material</TableCell>
                {options[0]?.weight_lb_ft && <TableCell>Weight (lb/ft)</TableCell>}
                {options[0]?.moment_capacity_ft_lb && <TableCell>Moment Capacity (ft-lb)</TableCell>}
              </TableRow>
            </TableHead>
            <TableBody>
              {options.map((option, idx) => (
                <TableRow key={idx}>
                  <TableCell>{option.shape || option.family || 'N/A'}</TableCell>
                  <TableCell>{option.size || option.designation || 'N/A'}</TableCell>
                  <TableCell>{option.material || 'N/A'}</TableCell>
                  {option.weight_lb_ft && (
                    <TableCell>{option.weight_lb_ft.toFixed(2)}</TableCell>
                  )}
                  {option.moment_capacity_ft_lb && (
                    <TableCell>{option.moment_capacity_ft_lb.toFixed(2)}</TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Paper>
  );
}