/**
 * Results Display - Beautiful presentation of backend calculations
 */

import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  Stack,
  Divider,
} from '@mui/material';
import {
  Download as DownloadIcon,
  ArrowBack as ArrowBackIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import type { ResponseEnvelope, CADExportResponse } from '../lib/api';

interface Props {
  results: ResponseEnvelope<CADExportResponse>;
  onBack: () => void;
  onDownload: () => void;
}

export default function ResultsDisplay({ results, onBack, onDownload }: Props) {
  const { result, assumptions, confidence, trace } = results;
  const intermediates = trace.data.intermediates;

  // Extract rebar schedule if available
  const rebarSchedule = intermediates.rebar_schedule as any;

  return (
    <Box>
      {/* Header */}
      <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 3 }}>
        <CheckCircleIcon color="success" sx={{ fontSize: 40 }} />
        <Box>
          <Typography variant="h5">Calculation Complete</Typography>
          <Typography variant="body2" color="text.secondary">
            File: {result.filename} • Size: {(result.file_size_bytes / 1024).toFixed(1)} KB • Entities: {result.num_entities}
          </Typography>
        </Box>
        <Box sx={{ flexGrow: 1 }} />
        <Chip
          label={`${(confidence * 100).toFixed(0)}% Confidence`}
          color={confidence >= 0.95 ? 'success' : 'warning'}
          variant="outlined"
        />
      </Stack>

      <Divider sx={{ mb: 3 }} />

      {/* Material Takeoff */}
      {rebarSchedule && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Material Takeoff (Order Quantities)
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2, bgcolor: 'primary.50' }}>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    Concrete
                  </Typography>
                  <Typography variant="h4" gutterBottom>
                    {rebarSchedule.concrete_cy_to_order || 'N/A'}
                    <Typography component="span" variant="subtitle1" sx={{ ml: 1 }}>
                      CY
                    </Typography>
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Includes 10% waste
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2, bgcolor: 'secondary.50' }}>
                  <Typography variant="subtitle2" color="secondary" gutterBottom>
                    Rebar
                  </Typography>
                  <Typography variant="h4" gutterBottom>
                    {rebarSchedule.rebar_ton_to_order
                      ? (rebarSchedule.rebar_ton_to_order * 2000).toFixed(0)
                      : 'N/A'}
                    <Typography component="span" variant="subtitle1" sx={{ ml: 1 }}>
                      lb
                    </Typography>
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Includes 5% waste
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Rebar Summary */}
      {rebarSchedule && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Rebar Schedule Summary
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Box sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Vertical Bars
                  </Typography>
                  <Typography variant="h6">
                    {rebarSchedule.vertical_bars} bars
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Horizontal Bars
                  </Typography>
                  <Typography variant="h6">
                    {rebarSchedule.horizontal_bars} bars
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Total Weight
                  </Typography>
                  <Typography variant="h6">
                    {rebarSchedule.total_weight_lb
                      ? rebarSchedule.total_weight_lb.toFixed(0)
                      : 'N/A'}{' '}
                    lb
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* CAD File Details */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            CAD File Details
          </Typography>
          <TableContainer>
            <Table size="small">
              <TableBody>
                <TableRow>
                  <TableCell>
                    <strong>Filename</strong>
                  </TableCell>
                  <TableCell>{result.filename}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>
                    <strong>Format</strong>
                  </TableCell>
                  <TableCell>
                    <Chip label={result.format.toUpperCase()} size="small" color="primary" />
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>
                    <strong>File Size</strong>
                  </TableCell>
                  <TableCell>{(result.file_size_bytes / 1024).toFixed(1)} KB</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>
                    <strong>Entities</strong>
                  </TableCell>
                  <TableCell>{result.num_entities} CAD entities</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>
                    <strong>Layers</strong>
                  </TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                      {result.layers.map((layer) => (
                        <Chip key={layer} label={layer} size="small" variant="outlined" />
                      ))}
                    </Stack>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Assumptions */}
      {assumptions.length > 0 && (
        <Alert severity="info" icon={<InfoIcon />} sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Engineering Assumptions
          </Typography>
          <Box component="ul" sx={{ mt: 1, mb: 0, pl: 2 }}>
            {assumptions.map((assumption, idx) => (
              <li key={idx}>
                <Typography variant="body2">{assumption}</Typography>
              </li>
            ))}
          </Box>
        </Alert>
      )}

      {/* Warnings */}
      {result.warnings.length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Warnings
          </Typography>
          <Box component="ul" sx={{ mt: 1, mb: 0, pl: 2 }}>
            {result.warnings.map((warning, idx) => (
              <li key={idx}>
                <Typography variant="body2">{warning}</Typography>
              </li>
            ))}
          </Box>
        </Alert>
      )}

      {/* Actions */}
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'space-between' }}>
        <Button variant="outlined" startIcon={<ArrowBackIcon />} onClick={onBack}>
          Back to Form
        </Button>
        <Button
          variant="contained"
          size="large"
          startIcon={<DownloadIcon />}
          onClick={onDownload}
        >
          Download DXF File
        </Button>
      </Box>
    </Box>
  );
}
