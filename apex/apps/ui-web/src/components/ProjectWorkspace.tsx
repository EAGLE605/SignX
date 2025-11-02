import { useEffect, lazy, Suspense } from 'react';
import { useParams, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { Box, Tabs, Tab, Paper, CircularProgress } from '@mui/material';
import { useProjectStore, type Stage } from '../store/projectStore';
import { ErrorBoundary } from './ErrorBoundary';
import StepperNavigation from './StepperNavigation';

// Lazy load stage components
const OverviewStage = lazy(() => import('./stages/OverviewStage'));
const SiteStage = lazy(() => import('./stages/SiteStage'));
const CabinetStage = lazy(() => import('./stages/CabinetStage'));
const StructuralStage = lazy(() => import('./stages/StructuralStage'));
const FoundationStage = lazy(() => import('./stages/FoundationStage'));
const FinalizationStage = lazy(() => import('./stages/FinalizationStage'));
const ReviewStage = lazy(() => import('./stages/ReviewStage'));
const SubmissionStage = lazy(() => import('./stages/SubmissionStage'));

const STAGES: Array<{ key: Stage; label: string; path: string }> = [
  { key: 'overview', label: 'Overview', path: 'overview' },
  { key: 'site', label: 'Site & Environmental', path: 'site' },
  { key: 'cabinet', label: 'Cabinet Design', path: 'cabinet' },
  { key: 'structural', label: 'Structural Design', path: 'structural' },
  { key: 'foundation', label: 'Foundation', path: 'foundation' },
  { key: 'finalization', label: 'Finalization', path: 'finalization' },
  { key: 'review', label: 'Review', path: 'review' },
  { key: 'submission', label: 'Submission', path: 'submission' },
];

const StageLoader = () => (
  <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
    <CircularProgress />
  </Box>
);

export default function ProjectWorkspace() {
  const { id, '*': path } = useParams<{ id: string; '*': string }>();
  const navigate = useNavigate();
  const { currentStage, setCurrentProject, setCurrentStage } = useProjectStore();

  useEffect(() => {
    if (id) {
      setCurrentProject(id);
      const pathMatch = path || 'overview';
      const stage = STAGES.find((s) => s.path === pathMatch);
      if (stage && stage.key !== currentStage) {
        setCurrentStage(stage.key);
      }
    }
  }, [id, path, setCurrentProject, setCurrentStage, currentStage]);

  const currentTabIndex = STAGES.findIndex((s) => s.key === currentStage);
  const handleTabChange = (_event: unknown, newValue: number) => {
    const stage = STAGES[newValue];
    if (stage) {
      setCurrentStage(stage.key);
      navigate(`/projects/${id}/${stage.path}`);
    }
  };

  return (
    <Box>
      <StepperNavigation stages={STAGES} />
      <Paper sx={{ mt: 2, mb: 2 }}>
        <Tabs
          value={currentTabIndex >= 0 ? currentTabIndex : 0}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          {STAGES.map((stage) => (
            <Tab key={stage.key} label={stage.label} />
          ))}
        </Tabs>
      </Paper>

      <Suspense fallback={<StageLoader />}>
        <ErrorBoundary>
          <Routes>
            <Route path="overview" element={<OverviewStage projectId={id || ''} />} />
            <Route path="site" element={<SiteStage projectId={id || ''} />} />
            <Route path="cabinet" element={<CabinetStage projectId={id || ''} />} />
            <Route path="structural" element={<StructuralStage projectId={id || ''} />} />
            <Route path="foundation" element={<FoundationStage projectId={id || ''} />} />
            <Route path="finalization" element={<FinalizationStage projectId={id || ''} />} />
            <Route path="review" element={<ReviewStage projectId={id || ''} />} />
            <Route path="submission" element={<SubmissionStage projectId={id || ''} />} />
            <Route path="*" element={<Navigate to="overview" replace />} />
          </Routes>
        </ErrorBoundary>
      </Suspense>
    </Box>
  );
}