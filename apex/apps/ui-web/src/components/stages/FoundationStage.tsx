import { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  Tabs,
  Tab,
  Grid,
} from '@mui/material';
import { api, APIError } from '../../api/client';
import { useProjectStore } from '../../store/projectStore';
import { useToast } from '../Toast';
import { parseEnvelope } from '../../utils/envelope';
import ConfidenceBadge from '../ConfidenceBadge';
import FileUpload from '../FileUpload';

interface FoundationStageProps {
  projectId: string;
}

interface BaseplateCheck {
  name: string;
  passed: boolean;
  message?: string;
}

export default function FoundationStage({ projectId }: FoundationStageProps) {
  const [foundationType, setFoundationType] = useState(0);
  const [diameter, setDiameter] = useState(18);
  const [depth, setDepth] = useState(3);
  const [plateThickness, setPlateThickness] = useState(0.5);
  const [weldSize, setWeldSize] = useState(0.25);
  const [anchors, setAnchors] = useState(4);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confidence, setConfidence] = useState<number | null>(null);
  const [baseplateChecks, setBaseplateChecks] = useState<BaseplateCheck[]>([]);
  const { updateProjectData, markStageComplete, projectData } = useProjectStore();
  const { showToast } = useToast();

  // Load saved data on mount
  useEffect(() => {
    const saved = projectData.foundation;
    if (saved) {
      setFoundationType(saved.type === 'baseplate' ? 1 : 0);
      setDiameter(saved.diameter_in || 18);
      setDepth(saved.depth_ft || 3);
      if ('plate_thickness_in' in saved) {
        setPlateThickness((saved.plate_thickness_in as number) || 0.5);
      }
      if ('weld_size_in' in saved) {
        setWeldSize((saved.weld_size_in as number) || 0.25);
      }
      if ('anchors' in saved) {
        setAnchors((saved.anchors as number) || 4);
      }
    }
  }, [projectData.foundation]);

  const handleSave = useCallback(async () => {
    try {
      if (foundationType === 0) {
        // Direct burial
        setLoading(true);
        const response = await api.solveFooting(diameter, depth);
        const parsed = parseEnvelope(response);
        setConfidence(parsed.confidence);

        if (parsed.warnings.length > 0) {
          parsed.warnings.forEach((w) => showToast(`Warning: ${w}`, 'warning'));
        }

        if (parsed.data) {
          updateProjectData('foundation', {
            type: 'direct_burial',
            diameter_in: diameter,
            depth_ft: depth,
            volume_ft3: parsed.data.volume_ft3,
            weight_lb: parsed.data.weight_lb,
          });
          markStageComplete('foundation');
          showToast('Foundation design saved', 'success');
        }

        if (parsed.requiresReview) {
          showToast('Engineering review recommended', 'warning');
        }
      } else {
        // Baseplate
        setLoading(true);
        const response = await api.checkBaseplate(plateThickness, weldSize, anchors);
        const parsed = parseEnvelope(response);
        setConfidence(parsed.confidence);

        if (parsed.data) {
          const checks = parsed.data.checks || [];
          setBaseplateChecks(checks as BaseplateCheck[]);

          // Show field errors for failing checks
          parsed.errors?.forEach((err) => {
            showToast(`Validation error: ${err.field}: ${err.message}`, 'error');
          });

          if (parsed.warnings.length > 0) {
            parsed.warnings.forEach((w) => showToast(`Warning: ${w}`, 'warning'));
          }

          updateProjectData('foundation', {
            type: 'baseplate',
            plate_thickness_in: plateThickness,
            weld_size_in: weldSize,
            anchors,
            checks,
            compliant: parsed.data.compliant,
          });

          if (parsed.data.compliant) {
            markStageComplete('foundation');
            showToast('Baseplate checks passed', 'success');
          } else {
            showToast('Baseplate checks failed - review required', 'warning');
          }
        }

        if (parsed.requiresReview) {
          showToast('Engineering review required due to low confidence', 'error');
        }
      }
    } catch (err) {
      const message =
        err instanceof APIError ? err.message : err instanceof Error ? err.message : 'Failed to save foundation';
      setError(message);
      showToast(message, 'error');
    } finally {
      setLoading(false);
    }
  }, [
    foundationType,
    diameter,
    depth,
    plateThickness,
    weldSize,
    anchors,
    updateProjectData,
    markStageComplete,
    showToast,
  ]);

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 2 }}>
        <Box display="flex" alignItems="center" gap={2} justifyContent="space-between" mb={2}>
          <Typography variant="h5">Foundation Design</Typography>
          {confidence !== null && <ConfidenceBadge confidence={confidence} />}
        </Box>

        <Tabs value={foundationType} onChange={(_, v) => setFoundationType(v)} sx={{ mt: 2 }}>
          <Tab label="Direct Burial" />
          <Tab label="Base Plate" />
        </Tabs>

        {foundationType === 0 && (
          <Grid container spacing={2} sx={{ mt: 2 }}>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Diameter (in)"
                type="number"
                value={diameter}
                onChange={(e) => setDiameter(Number(e.target.value))}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Depth (ft)"
                type="number"
                value={depth}
                onChange={(e) => setDepth(Number(e.target.value))}
              />
            </Grid>
          </Grid>
        )}

        {foundationType === 1 && (
          <Grid container spacing={2} sx={{ mt: 2 }}>
            <Grid item xs={4}>
              <TextField
                fullWidth
                label="Plate Thickness (in)"
                type="number"
                value={plateThickness}
                onChange={(e) => setPlateThickness(Number(e.target.value))}
              />
            </Grid>
            <Grid item xs={4}>
              <TextField
                fullWidth
                label="Weld Size (in)"
                type="number"
                value={weldSize}
                onChange={(e) => setWeldSize(Number(e.target.value))}
              />
            </Grid>
            <Grid item xs={4}>
              <TextField
                fullWidth
                label="Anchors"
                type="number"
                value={anchors}
                onChange={(e) => setAnchors(Number(e.target.value))}
              />
            </Grid>
          </Grid>
        )}

        {foundationType === 1 && baseplateChecks.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Validation Checks:
            </Typography>
            {baseplateChecks.map((check, idx) => (
              <Alert
                key={idx}
                severity={check.passed ? 'success' : 'error'}
                sx={{
                  mb: 1,
                  border: check.passed ? 'none' : '2px solid red',
                }}
              >
                {check.name}: {check.passed ? 'Passed' : `Failed${check.message ? ` - ${check.message}` : ''}`}
              </Alert>
            ))}
          </Box>
        )}

        <Button variant="contained" onClick={handleSave} disabled={loading} sx={{ mt: 2 }}>
          {loading ? 'Saving...' : 'Save Foundation Design'}
        </Button>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </Paper>

      <FileUpload projectId={projectId} />
    </Box>
  );
}