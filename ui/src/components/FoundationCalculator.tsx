/**
 * Foundation Calculator - Beautiful, Logical UI
 *
 * All complex engineering happens on the backend.
 * This component just collects inputs and displays beautiful results.
 */

import { useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Stepper,
  Step,
  StepLabel,
  Alert,
  CircularProgress,
  Divider,
  Chip,
  Stack,
} from '@mui/material';
import {
  Calculate as CalculateIcon,
  Download as DownloadIcon,
  Foundation as FoundationIcon,
  Build as BuildIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import {
  exportFoundationPlan,
  downloadFoundationPlanDXF,
  downloadBlob,
  type FoundationPlanRequest,
  type ResponseEnvelope,
  type CADExportResponse,
} from '../lib/api';
import ResultsDisplay from './ResultsDisplay';

// ============================================================================
// Validation Schema (type-safe with backend)
// ============================================================================

const foundationSchema = z.object({
  // Project info
  project_name: z.string().min(1, 'Project name required'),
  drawing_number: z.string().default('FND-001'),
  engineer: z.string().optional(),

  // Foundation parameters
  foundation_type: z.enum([
    'direct_burial',
    'pier_and_grade_beam',
    'drilled_shaft',
    'spread_footing',
    'mat_foundation',
  ]),
  diameter_ft: z.number().min(0.1).max(10),
  depth_ft: z.number().min(0.5).max(20),
  fc_ksi: z.number().min(2.5).max(10).default(3.0),
  fy_ksi: z.number().min(40).max(80).default(60),
  cover_in: z.number().min(1.5).max(6).default(3.0),

  // Anchor bolts (optional)
  include_anchors: z.boolean().default(false),
  num_bolts: z.number().min(4).max(12).optional(),
  bolt_diameter_in: z.number().min(0.5).max(3).optional(),
  bolt_circle_diameter_ft: z.number().min(1).max(10).optional(),
  projection_in: z.number().min(6).max(36).optional(),
  embedment_in: z.number().min(12).max(48).optional(),

  // Export options
  scale: z.enum(["1/4\"=1'-0\"", "1/2\"=1'-0\"", "1\"=1'-0\"", "3\"=1'-0\""]).default("1/4\"=1'-0\""),
});

type FoundationFormData = z.infer<typeof foundationSchema>;

// ============================================================================
// Component
// ============================================================================

export default function FoundationCalculator() {
  const [activeStep, setActiveStep] = useState(0);
  const [results, setResults] = useState<ResponseEnvelope<CADExportResponse> | null>(null);

  const {
    control,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FoundationFormData>({
    resolver: zodResolver(foundationSchema),
    defaultValues: {
      project_name: '',
      drawing_number: 'FND-001',
      engineer: '',
      foundation_type: 'direct_burial',
      diameter_ft: 3.0,
      depth_ft: 6.0,
      fc_ksi: 3.0,
      fy_ksi: 60,
      cover_in: 3.0,
      include_anchors: false,
      num_bolts: 8,
      bolt_diameter_in: 1.0,
      bolt_circle_diameter_ft: 2.5,
      projection_in: 12,
      embedment_in: 18,
      scale: "1/4\"=1'-0\"",
    },
  });

  const includeAnchors = watch('include_anchors');

  // Mutation for calculating and exporting
  const calculateMutation = useMutation({
    mutationFn: async (data: FoundationFormData) => {
      const request: FoundationPlanRequest = {
        foundation_type: data.foundation_type,
        diameter_ft: data.diameter_ft,
        depth_ft: data.depth_ft,
        fc_ksi: data.fc_ksi,
        fy_ksi: data.fy_ksi,
        cover_in: data.cover_in,
        project_name: data.project_name,
        drawing_number: data.drawing_number,
        engineer: data.engineer,
        scale: data.scale,
      };

      if (data.include_anchors) {
        request.anchor_layout = {
          num_bolts: data.num_bolts!,
          bolt_diameter_in: data.bolt_diameter_in!,
          bolt_circle_diameter_ft: data.bolt_circle_diameter_ft!,
          projection_in: data.projection_in!,
          embedment_in: data.embedment_in!,
        };
      }

      return exportFoundationPlan(request);
    },
    onSuccess: (data) => {
      setResults(data);
      setActiveStep(1); // Move to results step
    },
  });

  // Mutation for downloading DXF
  const downloadMutation = useMutation({
    mutationFn: async (data: FoundationFormData) => {
      const request: FoundationPlanRequest = {
        foundation_type: data.foundation_type,
        diameter_ft: data.diameter_ft,
        depth_ft: data.depth_ft,
        fc_ksi: data.fc_ksi,
        fy_ksi: data.fy_ksi,
        cover_in: data.cover_in,
        project_name: data.project_name,
        drawing_number: data.drawing_number,
        engineer: data.engineer,
        scale: data.scale,
      };

      if (data.include_anchors) {
        request.anchor_layout = {
          num_bolts: data.num_bolts!,
          bolt_diameter_in: data.bolt_diameter_in!,
          bolt_circle_diameter_ft: data.bolt_circle_diameter_ft!,
          projection_in: data.projection_in!,
          embedment_in: data.embedment_in!,
        };
      }

      return downloadFoundationPlanDXF(request);
    },
    onSuccess: (blob, variables) => {
      const filename = `${variables.drawing_number.replace('/', '_')}_foundation_plan.dxf`;
      downloadBlob(blob, filename);
    },
  });

  const onSubmit = (data: FoundationFormData) => {
    calculateMutation.mutate(data);
  };

  const onDownload = (data: FoundationFormData) => {
    downloadMutation.mutate(data);
  };

  const steps = ['Input Parameters', 'Review Results'];

  return (
    <Paper sx={{ p: 3 }}>
      {/* Stepper */}
      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {activeStep === 0 && (
        <Box component="form" onSubmit={handleSubmit(onSubmit)}>
          {/* Project Information */}
          <Box sx={{ mb: 4 }}>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
              <DescriptionIcon color="primary" />
              <Typography variant="h6">Project Information</Typography>
            </Stack>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Controller
                  name="project_name"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Project Name"
                      fullWidth
                      required
                      error={!!errors.project_name}
                      helperText={errors.project_name?.message}
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <Controller
                  name="drawing_number"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Drawing Number"
                      fullWidth
                      error={!!errors.drawing_number}
                      helperText={errors.drawing_number?.message}
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <Controller
                  name="engineer"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Engineer (P.E.)"
                      fullWidth
                      placeholder="Optional"
                    />
                  )}
                />
              </Grid>
            </Grid>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Foundation Parameters */}
          <Box sx={{ mb: 4 }}>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
              <FoundationIcon color="primary" />
              <Typography variant="h6">Foundation Parameters</Typography>
            </Stack>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Controller
                  name="foundation_type"
                  control={control}
                  render={({ field }) => (
                    <FormControl fullWidth>
                      <InputLabel>Foundation Type</InputLabel>
                      <Select {...field} label="Foundation Type">
                        <MenuItem value="direct_burial">Direct Burial</MenuItem>
                        <MenuItem value="pier_and_grade_beam">Pier and Grade Beam</MenuItem>
                        <MenuItem value="drilled_shaft">Drilled Shaft</MenuItem>
                        <MenuItem value="spread_footing">Spread Footing</MenuItem>
                        <MenuItem value="mat_foundation">Mat Foundation</MenuItem>
                      </Select>
                    </FormControl>
                  )}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <Controller
                  name="diameter_ft"
                  control={control}
                  render={({ field: { onChange, value, ...field } }) => (
                    <TextField
                      {...field}
                      value={value}
                      onChange={(e) => onChange(parseFloat(e.target.value))}
                      label="Diameter"
                      type="number"
                      fullWidth
                      InputProps={{ endAdornment: 'ft' }}
                      inputProps={{ step: 0.5, min: 0.1, max: 10 }}
                      error={!!errors.diameter_ft}
                      helperText={errors.diameter_ft?.message || '0.1 - 10 ft'}
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <Controller
                  name="depth_ft"
                  control={control}
                  render={({ field: { onChange, value, ...field } }) => (
                    <TextField
                      {...field}
                      value={value}
                      onChange={(e) => onChange(parseFloat(e.target.value))}
                      label="Depth"
                      type="number"
                      fullWidth
                      InputProps={{ endAdornment: 'ft' }}
                      inputProps={{ step: 0.5, min: 0.5, max: 20 }}
                      error={!!errors.depth_ft}
                      helperText={errors.depth_ft?.message || '0.5 - 20 ft'}
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <Controller
                  name="fc_ksi"
                  control={control}
                  render={({ field: { onChange, value, ...field } }) => (
                    <TextField
                      {...field}
                      value={value}
                      onChange={(e) => onChange(parseFloat(e.target.value))}
                      label="Concrete Strength (f'c)"
                      type="number"
                      fullWidth
                      InputProps={{ endAdornment: 'ksi' }}
                      inputProps={{ step: 0.5, min: 2.5, max: 10 }}
                      error={!!errors.fc_ksi}
                      helperText={errors.fc_ksi?.message || 'Typical: 3.0 - 4.0 ksi'}
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <Controller
                  name="fy_ksi"
                  control={control}
                  render={({ field: { onChange, value, ...field } }) => (
                    <TextField
                      {...field}
                      value={value}
                      onChange={(e) => onChange(parseFloat(e.target.value))}
                      label="Rebar Yield (fy)"
                      type="number"
                      fullWidth
                      InputProps={{ endAdornment: 'ksi' }}
                      inputProps={{ step: 10, min: 40, max: 80 }}
                      error={!!errors.fy_ksi}
                      helperText={errors.fy_ksi?.message || 'Grade 60: 60 ksi'}
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <Controller
                  name="cover_in"
                  control={control}
                  render={({ field: { onChange, value, ...field } }) => (
                    <TextField
                      {...field}
                      value={value}
                      onChange={(e) => onChange(parseFloat(e.target.value))}
                      label="Concrete Cover"
                      type="number"
                      fullWidth
                      InputProps={{ endAdornment: 'in' }}
                      inputProps={{ step: 0.5, min: 1.5, max: 6 }}
                      error={!!errors.cover_in}
                      helperText={errors.cover_in?.message || 'ACI: 3" typical'}
                    />
                  )}
                />
              </Grid>
            </Grid>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Anchor Bolts */}
          <Box sx={{ mb: 4 }}>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
              <BuildIcon color="primary" />
              <Typography variant="h6">Anchor Bolts (Optional)</Typography>
            </Stack>
            <Controller
              name="include_anchors"
              control={control}
              render={({ field }) => (
                <FormControlLabel
                  control={<Checkbox {...field} checked={field.value} />}
                  label="Include anchor bolt layout"
                />
              )}
            />
            {includeAnchors && (
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12} md={4}>
                  <Controller
                    name="num_bolts"
                    control={control}
                    render={({ field: { onChange, value, ...field } }) => (
                      <TextField
                        {...field}
                        value={value}
                        onChange={(e) => onChange(parseInt(e.target.value))}
                        label="Number of Bolts"
                        type="number"
                        fullWidth
                        inputProps={{ step: 1, min: 4, max: 12 }}
                        error={!!errors.num_bolts}
                        helperText={errors.num_bolts?.message || '4 - 12 bolts'}
                      />
                    )}
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <Controller
                    name="bolt_diameter_in"
                    control={control}
                    render={({ field: { onChange, value, ...field } }) => (
                      <TextField
                        {...field}
                        value={value}
                        onChange={(e) => onChange(parseFloat(e.target.value))}
                        label="Bolt Diameter"
                        type="number"
                        fullWidth
                        InputProps={{ endAdornment: 'in' }}
                        inputProps={{ step: 0.125, min: 0.5, max: 3 }}
                        error={!!errors.bolt_diameter_in}
                        helperText={errors.bolt_diameter_in?.message || '0.5 - 3 in'}
                      />
                    )}
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <Controller
                    name="bolt_circle_diameter_ft"
                    control={control}
                    render={({ field: { onChange, value, ...field } }) => (
                      <TextField
                        {...field}
                        value={value}
                        onChange={(e) => onChange(parseFloat(e.target.value))}
                        label="Bolt Circle Diameter"
                        type="number"
                        fullWidth
                        InputProps={{ endAdornment: 'ft' }}
                        inputProps={{ step: 0.25, min: 1, max: 10 }}
                        error={!!errors.bolt_circle_diameter_ft}
                        helperText={errors.bolt_circle_diameter_ft?.message}
                      />
                    )}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Controller
                    name="projection_in"
                    control={control}
                    render={({ field: { onChange, value, ...field } }) => (
                      <TextField
                        {...field}
                        value={value}
                        onChange={(e) => onChange(parseFloat(e.target.value))}
                        label="Projection Above Concrete"
                        type="number"
                        fullWidth
                        InputProps={{ endAdornment: 'in' }}
                        inputProps={{ step: 1, min: 6, max: 36 }}
                        error={!!errors.projection_in}
                        helperText={errors.projection_in?.message}
                      />
                    )}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Controller
                    name="embedment_in"
                    control={control}
                    render={({ field: { onChange, value, ...field } }) => (
                      <TextField
                        {...field}
                        value={value}
                        onChange={(e) => onChange(parseFloat(e.target.value))}
                        label="Embedment Depth"
                        type="number"
                        fullWidth
                        InputProps={{ endAdornment: 'in' }}
                        inputProps={{ step: 1, min: 12, max: 48 }}
                        error={!!errors.embedment_in}
                        helperText={errors.embedment_in?.message}
                      />
                    )}
                  />
                </Grid>
              </Grid>
            )}
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Export Options */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Drawing Options
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Controller
                  name="scale"
                  control={control}
                  render={({ field }) => (
                    <FormControl fullWidth>
                      <InputLabel>Drawing Scale</InputLabel>
                      <Select {...field} label="Drawing Scale">
                        <MenuItem value="1/4\"=1'-0\"">1/4" = 1'-0" (Standard)</MenuItem>
                        <MenuItem value="1/2\"=1'-0\"">1/2" = 1'-0" (Large)</MenuItem>
                        <MenuItem value="1\"=1'-0\"">1" = 1'-0" (Extra Large)</MenuItem>
                        <MenuItem value="3\"=1'-0\"">3" = 1'-0" (Detail)</MenuItem>
                      </Select>
                    </FormControl>
                  )}
                />
              </Grid>
            </Grid>
          </Box>

          {/* Error Display */}
          {calculateMutation.isError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Calculation failed: {calculateMutation.error instanceof Error ? calculateMutation.error.message : 'Unknown error'}
            </Alert>
          )}

          {/* Action Buttons */}
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              size="large"
              onClick={handleSubmit(onDownload)}
              disabled={downloadMutation.isPending}
              startIcon={downloadMutation.isPending ? <CircularProgress size={20} /> : <DownloadIcon />}
            >
              {downloadMutation.isPending ? 'Generating...' : 'Quick Download DXF'}
            </Button>
            <Button
              variant="contained"
              size="large"
              type="submit"
              disabled={calculateMutation.isPending}
              startIcon={calculateMutation.isPending ? <CircularProgress size={20} /> : <CalculateIcon />}
            >
              {calculateMutation.isPending ? 'Calculating...' : 'Calculate & Preview'}
            </Button>
          </Box>
        </Box>
      )}

      {activeStep === 1 && results && (
        <ResultsDisplay
          results={results}
          onBack={() => setActiveStep(0)}
          onDownload={handleSubmit(onDownload)}
        />
      )}
    </Paper>
  );
}
