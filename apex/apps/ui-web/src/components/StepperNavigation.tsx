import { Paper, Stepper, Step, StepLabel, StepButton, Box, Chip, useMediaQuery, useTheme, Typography } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import { useProjectStore, type Stage } from '../store/projectStore';
import { validateStage } from '../utils/validation';

interface StepperNavigationProps {
  stages: Array<{ key: Stage; label: string; path: string }>;
}

export default function StepperNavigation({ stages }: StepperNavigationProps) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { currentStage, completedStages, projectData, setCurrentStage } = useProjectStore();

  const currentIndex = stages.findIndex((s) => s.key === currentStage);
  const activeStep = currentIndex >= 0 ? currentIndex : 0;

  const handleStepClick = (index: number) => {
    const stage = stages[index];
    if (stage) {
      const validation = validateStage(stage.key, projectData);
      if (!validation.isValid && !completedStages.has(stage.key)) {
        console.warn('Stage validation errors:', validation.errors);
      }
      setCurrentStage(stage.key);
    }
  };

  const getStepStatus = (stage: Stage) => {
    if (completedStages.has(stage)) {
      return 'completed';
    }
    const validation = validateStage(stage, projectData);
    if (!validation.isValid) {
      return 'error';
    }
    return 'pending';
  };

  // Mobile: Show compact horizontal scrollable stepper
  if (isMobile) {
    return (
      <Paper sx={{ p: 2, mb: 2, overflowX: 'auto' }}>
        <Box
          sx={{
            display: 'flex',
            gap: 1,
            minWidth: 'max-content',
            pb: 1,
          }}
          role="navigation"
          aria-label="Project stages"
        >
          {stages.map((stage, index) => {
            const status = getStepStatus(stage.key);
            const isActive = index === activeStep;

            return (
              <Box
                key={stage.key}
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  minWidth: 80,
                  cursor: 'pointer',
                  p: 1,
                  borderRadius: 1,
                  bgcolor: isActive ? 'action.selected' : 'transparent',
                  border: isActive ? '2px solid' : '2px solid transparent',
                  borderColor: isActive ? 'primary.main' : 'transparent',
                }}
                onClick={() => handleStepClick(index)}
                role="button"
                tabIndex={0}
                aria-label={`Stage ${index + 1}: ${stage.label}${status === 'completed' ? ', completed' : status === 'error' ? ', has errors' : ''}`}
                aria-current={isActive ? 'step' : undefined}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleStepClick(index);
                  }
                }}
              >
                {status === 'completed' ? (
                  <CheckCircleIcon color="success" fontSize="small" />
                ) : status === 'error' ? (
                  <ErrorIcon color="error" fontSize="small" />
                ) : (
                  <Box
                    sx={{
                      width: 24,
                      height: 24,
                      borderRadius: '50%',
                      border: '2px solid',
                      borderColor: isActive ? 'primary.main' : 'text.secondary',
                      bgcolor: isActive ? 'primary.main' : 'transparent',
                    }}
                  />
                )}
                <Typography variant="caption" sx={{ mt: 0.5, textAlign: 'center', fontSize: '0.7rem' }}>
                  {stage.label}
                </Typography>
              </Box>
            );
          })}
        </Box>
      </Paper>
    );
  }

  // Desktop: Full stepper
  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Stepper activeStep={activeStep} alternativeLabel role="navigation" aria-label="Project stages">
        {stages.map((stage, index) => {
          const status = getStepStatus(stage.key);
          const isActive = index === activeStep;

          return (
            <Step
              key={stage.key}
              completed={status === 'completed'}
              sx={{
                '& .MuiStepLabel-root': {
                  '& .MuiStepLabel-label': {
                    color: status === 'error' && !isActive ? 'error.main' : undefined,
                  },
                },
              }}
            >
              <StepButton
                onClick={() => handleStepClick(index)}
                icon={
                  status === 'completed' ? (
                    <CheckCircleIcon color="success" />
                  ) : status === 'error' ? (
                    <ErrorIcon color="error" />
                  ) : undefined
                }
                aria-label={`Stage ${index + 1}: ${stage.label}${status === 'completed' ? ', completed' : status === 'error' ? ', has errors' : ''}`}
                aria-current={isActive ? 'step' : undefined}
              >
                <StepLabel>
                  {stage.label}
                  {status === 'error' && (
                    <Chip
                      label="Incomplete"
                      size="small"
                      color="error"
                      sx={{ ml: 1, height: 20, fontSize: '0.65rem' }}
                      aria-label="This stage has validation errors"
                    />
                  )}
                </StepLabel>
              </StepButton>
            </Step>
          );
        })}
      </Stepper>
    </Paper>
  );
}