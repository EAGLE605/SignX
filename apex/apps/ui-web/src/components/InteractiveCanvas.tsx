import { useState, useRef, useCallback, useEffect, memo } from 'react';
import { Stage, Layer, Rect, Transformer, Line } from 'react-konva';
import type Konva from 'konva';
import {
  Box,
  Paper,
  Typography,
  TextField,
  CircularProgress,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  ButtonGroup,
} from '@mui/material';
import UndoIcon from '@mui/icons-material/Undo';
import RedoIcon from '@mui/icons-material/Redo';
import StraightenIcon from '@mui/icons-material/Straighten';
import DownloadIcon from '@mui/icons-material/Download';
import { useProjectStore } from '../store/projectStore';
import { api, APIError } from '../api/client';
import { debounce } from '../utils/debounce';
import { useToast } from './Toast';
import ConfidenceBadge from './ConfidenceBadge';
import { parseEnvelope } from '../utils/envelope';
import { useUndoRedo } from '../hooks/useUndoRedo';
import { analytics, trackEvent } from '../utils/analytics';
import type { CanvasDimension } from '../types/api';

interface InteractiveCanvasProps {
  width?: number;
  height?: number;
}

interface CanvasState {
  rectSize: { x: number; y: number; width: number; height: number };
  snapToGrid: boolean;
}

function InteractiveCanvasComponent({
  width = 800,
  height = 600,
}: InteractiveCanvasProps) {
  const { canvasDimensions, setCanvasDimensions } = useProjectStore();
  const { showToast } = useToast();
  const [rectSize, setRectSize] = useState({
    x: canvasDimensions?.x || 50,
    y: canvasDimensions?.y || 50,
    width: canvasDimensions?.width || 200,
    height: canvasDimensions?.height || 150,
  });
  const [isSelected, setIsSelected] = useState(false);
  const [isDeriving, setIsDeriving] = useState(false);
  const [confidence, setConfidence] = useState<number | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [snapToGrid, setSnapToGrid] = useState(false);
  const [showGrid, setShowGrid] = useState(false);
  const [measurementMode, setMeasurementMode] = useState(false);
  const [measurePoints, setMeasurePoints] = useState<Array<{ x: number; y: number }>>([]);
  const transformerRef = useRef<Konva.Transformer | null>(null);
  const rectRef = useRef<Konva.Rect | null>(null);
  const deriveAbortController = useRef<AbortController | null>(null);
  const cacheKeyRef = useRef<string>('');

  // Undo/Redo
  const initialState: CanvasState = {
    rectSize: {
      x: canvasDimensions?.x || 50,
      y: canvasDimensions?.y || 50,
      width: canvasDimensions?.width || 200,
      height: canvasDimensions?.height || 150,
    },
    snapToGrid: false,
  };

  const { state: historyState, setState: pushHistory, undo, redo, canUndo, canRedo } =
    useUndoRedo<CanvasState>(initialState);

  // Sync history state to current state
  useEffect(() => {
    setRectSize(historyState.rectSize);
    setSnapToGrid(historyState.snapToGrid);
  }, [historyState]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        if (undo()) {
          showToast('Undone', 'info');
          const projectId = useProjectStore.getState().currentProjectId || 'current';
          analytics.deriveUsed(projectId, { width: rectSize.width, height: rectSize.height });
        }
      } else if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        if (redo()) {
          showToast('Redone', 'info');
        }
      } else if (e.key === 'Escape') {
        setIsSelected(false);
        setMeasurementMode(false);
        setMeasurePoints([]);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [undo, redo, showToast, rectSize]);

  const snapValue = useCallback((value: number, gridSize = 10) => {
    if (!snapToGrid) return value;
    return Math.round(value / gridSize) * gridSize;
  }, [snapToGrid]);

  // Debounced derive function (300ms)
  const debouncedDerive = useCallback(
    debounce(async (dimensions: { width: number; height: number }) => {
      if (deriveAbortController.current) {
        deriveAbortController.current.abort();
      }

      deriveAbortController.current = new AbortController();
      setIsDeriving(true);
      setWarnings([]);

      try {
        const width_in = Math.max(1, Math.round(dimensions.width / 10));
        const height_in = Math.max(1, Math.round(dimensions.height / 10));

        const startTime = performance.now();
        const response = await api.deriveCabinet(
          {
            width_in,
            height_in,
            depth_in: 12,
            density_lb_ft3: 50,
          },
          cacheKeyRef.current || undefined,
        );
        const latency = performance.now() - startTime;

        // Track performance
        if (window.Sentry) {
          window.Sentry.addBreadcrumb({
            category: 'performance',
            message: 'derive_operation',
            data: { latency_ms: latency },
            level: 'info',
          });
        }

        const parsed = parseEnvelope(response);
        setConfidence(parsed.confidence);

        if (parsed.contentSha256) {
          cacheKeyRef.current = parsed.contentSha256;
        }

        if (parsed.warnings.length > 0) {
          setWarnings(parsed.warnings);
          parsed.warnings.forEach((warning) => {
            showToast(`Warning: ${warning}`, 'warning');
          });
          analytics.lowConfidenceWarning('canvas', parsed.confidence);
        }

        if (parsed.data) {
          const derived = parsed.data;
          const area = derived.area_ft2 || derived.A_ft2;
          if (area) {
            const side_in = Math.sqrt(area * 144);
            const newRectSize = {
              ...rectSize,
              width: side_in * 10,
              height: side_in * 10,
            };
            setRectSize(newRectSize);
            pushHistory({
              rectSize: newRectSize,
              snapToGrid,
            });
            showToast('Dimensions updated from backend calculation', 'success');
          }
        }

        if (parsed.requiresReview) {
          showToast('Engineering review recommended due to low confidence', 'warning');
        }

        const projectId = useProjectStore.getState().currentProjectId || 'current';
        analytics.deriveUsed(projectId, { width: width_in, height: height_in });
      } catch (error) {
        if (error instanceof Error && error.name !== 'AbortError') {
          const message =
            error instanceof APIError ? error.message : error.message || 'Failed to derive dimensions';
          showToast(message, 'error');
          analytics.errorOccurred('derive_failed', { error: message });

          if (error instanceof APIError && error.fieldErrors) {
            error.fieldErrors.forEach((err) => {
              showToast(`Validation error: ${err.field}: ${err.message}`, 'error');
            });
          }

          if (error instanceof APIError && error.warnings) {
            error.warnings.forEach((warning) => {
              showToast(`Warning: ${warning}`, 'warning');
            });
          }
        }
      } finally {
        setIsDeriving(false);
      }
    }, 300),
    [showToast, rectSize, snapToGrid, pushHistory],
  );

  const handleSelect = useCallback(() => {
    setIsSelected(true);
    if (transformerRef.current && rectRef.current) {
      transformerRef.current.nodes([rectRef.current]);
      transformerRef.current.getLayer()?.batchDraw();
    }
  }, []);

  const handleTransformEnd = useCallback(() => {
    if (!rectRef.current) return;

    const node = rectRef.current;
    const scaleX = node.scaleX();
    const scaleY = node.scaleY();

    const newDimensions = {
      x: snapValue(node.x()),
      y: snapValue(node.y()),
      width: Math.max(50, snapValue(node.width() * scaleX)),
      height: Math.max(50, snapValue(node.height() * scaleY)),
    };

    setRectSize(newDimensions);
    pushHistory({
      rectSize: newDimensions,
      snapToGrid,
    });

    node.scaleX(1);
    node.scaleY(1);

    const canvasDims: CanvasDimension = {
      x: newDimensions.x,
      y: newDimensions.y,
      width: newDimensions.width,
      height: newDimensions.height,
    };

    setCanvasDimensions(canvasDims);
    debouncedDerive({ width: newDimensions.width, height: newDimensions.height });
  }, [setCanvasDimensions, debouncedDerive, snapToGrid, pushHistory, snapValue]);

  const handleManualUpdate = useCallback(
    (field: 'x' | 'y' | 'width' | 'height', value: number) => {
      const snappedValue = snapValue(Math.max(0, value));
      const updated = { ...rectSize, [field]: snappedValue };
      setRectSize(updated);
      pushHistory({
        rectSize: updated,
        snapToGrid,
      });

      setCanvasDimensions({
        x: updated.x,
        y: updated.y,
        width: updated.width,
        height: updated.height,
      });

      if (rectRef.current) {
        rectRef.current.setAttrs({
          x: updated.x,
          y: updated.y,
          width: updated.width,
          height: updated.height,
        });
        transformerRef.current?.getLayer()?.batchDraw();
      }

      if (field === 'width' || field === 'height') {
        debouncedDerive({ width: updated.width, height: updated.height });
      }
    },
    [rectSize, setCanvasDimensions, debouncedDerive, snapToGrid, pushHistory, snapValue],
  );

  const handleCanvasClick = useCallback(
    (e: Konva.KonvaEventObject<MouseEvent>) => {
      if (!measurementMode) return;

      const stage = e.target.getStage();
      const point = stage.getPointerPosition();
      const newPoints = [...measurePoints, { x: point.x, y: point.y }];

      if (newPoints.length >= 2) {
        const [p1, p2] = newPoints.slice(-2);
        const distance = Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2));
        showToast(`Distance: ${distance.toFixed(2)}px (${(distance / 10).toFixed(2)}in)`, 'info');
        setMeasurePoints([]);
      } else {
        setMeasurePoints(newPoints);
      }
    },
    [measurementMode, measurePoints, showToast],
  );

  const handleExport = useCallback(() => {
    const stage = rectRef.current?.getStage();
    if (!stage) return;

    const dataURL = stage.toDataURL({ pixelRatio: 2 });
    const link = document.createElement('a');
    link.download = `canvas-export-${Date.now()}.png`;
    link.href = dataURL;
    link.click();

    trackEvent('canvas_exported', { format: 'png' });
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (deriveAbortController.current) {
        deriveAbortController.current.abort();
      }
    };
  }, []);

  // Grid lines
  const gridLines = showGrid
    ? Array.from({ length: Math.ceil(width / 10) }, (_, i) => (
        <Line
          key={`v-${i}`}
          points={[i * 10, 0, i * 10, height]}
          stroke="#e0e0e0"
          strokeWidth={0.5}
          listening={false}
        />
      )).concat(
        Array.from({ length: Math.ceil(height / 10) }, (_, i) => (
          <Line
            key={`h-${i}`}
            points={[0, i * 10, width, i * 10]}
            stroke="#e0e0e0"
            strokeWidth={0.5}
            listening={false}
          />
        )),
      )
    : [];

  // Measurement lines
  const measurementLines =
    measurePoints.length >= 2
      ? measurePoints.slice(-2).map((_p, idx, arr) =>
          idx === 0 ? (
            <Line
              key={`measure-${idx}`}
              points={[arr[0].x, arr[0].y, arr[1].x, arr[1].y]}
              stroke="#ff5722"
              strokeWidth={2}
              dash={[5, 5]}
              listening={false}
            />
          ) : null,
        )
      : [];

  return (
    <Box>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box display="flex" alignItems="center" gap={2} justifyContent="space-between" flexWrap="wrap">
          <Box>
            <Typography variant="h6">2D Interactive Canvas</Typography>
            {isDeriving && (
              <Box display="flex" alignItems="center" gap={1}>
                <CircularProgress size={16} aria-label="Calculating" />
                <Typography variant="caption" color="text.secondary">
                  Calculating...
                </Typography>
              </Box>
            )}
          </Box>
          {confidence !== null && <ConfidenceBadge confidence={confidence} />}
        </Box>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Drag to move, resize handles to adjust dimensions. Changes sync automatically.
        </Typography>

        {/* Toolbar */}
        <Box display="flex" gap={1} mt={2} flexWrap="wrap" alignItems="center">
          <ButtonGroup size="small" variant="outlined">
            <Tooltip title="Undo (Ctrl+Z)" aria-label="Undo">
              <IconButton onClick={undo} disabled={!canUndo} size="small">
                <UndoIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Redo (Ctrl+Shift+Z)" aria-label="Redo">
              <IconButton onClick={redo} disabled={!canRedo} size="small">
                <RedoIcon />
              </IconButton>
            </Tooltip>
          </ButtonGroup>

          <FormControlLabel
            control={
              <Switch
                checked={snapToGrid}
                onChange={(e) => {
                  setSnapToGrid(e.target.checked);
                  pushHistory({ rectSize, snapToGrid: e.target.checked });
                }}
                size="small"
              />
            }
            label="Snap to Grid"
          />

          <FormControlLabel
            control={
              <Switch
                checked={showGrid}
                onChange={(e) => setShowGrid(e.target.checked)}
                size="small"
              />
            }
            label="Show Grid"
          />

          <Tooltip title="Measurement Tool (Click two points)" aria-label="Measurement tool">
            <IconButton
              onClick={() => {
                setMeasurementMode(!measurementMode);
                setMeasurePoints([]);
              }}
              color={measurementMode ? 'primary' : 'default'}
              size="small"
            >
              <StraightenIcon />
            </IconButton>
          </Tooltip>

          <Tooltip title="Export as PNG" aria-label="Export canvas">
            <IconButton onClick={handleExport} size="small">
              <DownloadIcon />
            </IconButton>
          </Tooltip>
        </Box>

        {warnings.length > 0 && (
          <Box sx={{ mt: 1 }}>
            {warnings.map((warning, idx) => (
              <Typography
                key={idx}
                variant="caption"
                color="warning.main"
                sx={{ display: 'block' }}
                role="alert"
                aria-live="polite"
              >
                ⚠ {warning}
              </Typography>
            ))}
          </Box>
        )}

        {measurementMode && (
          <Typography variant="caption" color="info.main" sx={{ mt: 1, display: 'block' }}>
            Click two points to measure distance. Press Escape to cancel.
          </Typography>
        )}
      </Paper>

      <Box display="flex" gap={2} flexDirection={{ xs: 'column', md: 'row' }}>
        <Paper sx={{ p: 2, flex: 1, position: 'relative' }}>
          {isDeriving && (
            <Box
              sx={{
                position: 'absolute',
                top: 8,
                right: 8,
                zIndex: 10,
                bgcolor: 'background.paper',
                p: 1,
                borderRadius: 1,
              }}
              role="status"
              aria-label="Deriving dimensions"
            >
              <CircularProgress size={20} aria-hidden="true" />
            </Box>
          )}
          <Stage
            width={width}
            height={height}
            onMouseDown={(e) => {
              const clickedOnEmpty = e.target === e.target.getStage();
              if (clickedOnEmpty && !measurementMode) {
                setIsSelected(false);
              }
              if (measurementMode) {
                handleCanvasClick(e);
              }
            }}
            onTouchStart={(e) => {
              // Handle touch for mobile
              const clickedOnEmpty = e.target === e.target.getStage();
              if (clickedOnEmpty && !measurementMode) {
                setIsSelected(false);
              }
              if (measurementMode) {
                handleCanvasClick(e);
              }
            }}
            tabIndex={0}
            role="application"
            aria-label="Interactive 2D canvas for sign dimensions"
          >
            <Layer>
              {gridLines}
              {measurementLines}
              <Rect
                ref={rectRef}
                x={rectSize.x}
                y={rectSize.y}
                width={rectSize.width}
                height={rectSize.height}
                fill="#1976d2"
                opacity={isDeriving ? 0.5 : 0.7}
                draggable
                onClick={handleSelect}
                onTap={handleSelect}
                onDragEnd={(e) => {
                  const updated = {
                    ...rectSize,
                    x: snapValue(e.target.x()),
                    y: snapValue(e.target.y()),
                  };
                  setRectSize(updated);
                  pushHistory({
                    rectSize: updated,
                    snapToGrid,
                  });
                  setCanvasDimensions({
                    x: updated.x,
                    y: updated.y,
                    width: updated.width,
                    height: updated.height,
                  });
                }}
                onTransformEnd={handleTransformEnd}
                aria-label={`Rectangle at position ${Math.round(rectSize.x)}, ${Math.round(rectSize.y)} with dimensions ${Math.round(rectSize.width)} by ${Math.round(rectSize.height)}`}
              />
              {isSelected && (
                <Transformer
                  ref={transformerRef}
                  boundBoxFunc={(oldBox, newBox) => {
                    if (Math.abs(newBox.width) < 50 || Math.abs(newBox.height) < 50) {
                      return oldBox;
                    }
                    return newBox;
                  }}
                />
              )}
            </Layer>
          </Stage>
        </Paper>

        <Paper sx={{ p: 2, minWidth: 250 }}>
          <Typography variant="subtitle2" gutterBottom>
            Dimensions
          </Typography>
          <Box display="flex" flexDirection="column" gap={2} mt={1} role="group" aria-label="Dimension inputs">
            <TextField
              label="X Position"
              type="number"
              size="small"
              value={Math.round(rectSize.x)}
              onChange={(e) => handleManualUpdate('x', Number(e.target.value))}
              disabled={isDeriving}
              aria-describedby="x-position-desc"
            />
            <Typography id="x-position-desc" variant="caption" sx={{ display: 'none' }}>
              X coordinate in pixels
            </Typography>
            <TextField
              label="Y Position"
              type="number"
              size="small"
              value={Math.round(rectSize.y)}
              onChange={(e) => handleManualUpdate('y', Number(e.target.value))}
              disabled={isDeriving}
              aria-describedby="y-position-desc"
            />
            <Typography id="y-position-desc" variant="caption" sx={{ display: 'none' }}>
              Y coordinate in pixels
            </Typography>
            <TextField
              label="Width"
              type="number"
              size="small"
              value={Math.round(rectSize.width)}
              onChange={(e) => handleManualUpdate('width', Number(e.target.value))}
              disabled={isDeriving}
              aria-describedby="width-desc"
            />
            <Typography id="width-desc" variant="caption" sx={{ display: 'none' }}>
              Width in pixels, automatically synced with backend
            </Typography>
            <TextField
              label="Height"
              type="number"
              size="small"
              value={Math.round(rectSize.height)}
              onChange={(e) => handleManualUpdate('height', Number(e.target.value))}
              disabled={isDeriving}
              aria-describedby="height-desc"
            />
            <Typography id="height-desc" variant="caption" sx={{ display: 'none' }}>
              Height in pixels, automatically synced with backend
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Box>
  );
}

export default memo(InteractiveCanvasComponent);