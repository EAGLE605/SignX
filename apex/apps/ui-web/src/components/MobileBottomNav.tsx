import { useNavigate, useLocation } from 'react-router-dom';
import { BottomNavigation, BottomNavigationAction, Paper } from '@mui/material';
import { useMediaQuery, useTheme } from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import ExploreIcon from '@mui/icons-material/Explore';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import AssessmentIcon from '@mui/icons-material/Assessment';
import { useProjectStore } from '../store/projectStore';

export default function MobileBottomNav() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const location = useLocation();
  const { currentStage } = useProjectStore();

  if (!isMobile) return null;

  const getStagePath = (stage: string) => {
    const projectMatch = location.pathname.match(/\/projects\/([^/]+)/);
    if (projectMatch) {
      return `/projects/${projectMatch[1]}/${stage}`;
    }
    return '/';
  };

  const handleChange = (_event: unknown, newValue: string) => {
    if (newValue === 'home') {
      navigate('/');
    } else {
      navigate(getStagePath(newValue));
    }
  };

  const getCurrentValue = () => {
    if (location.pathname === '/') return 'home';
    const stageMap: Record<string, string> = {
      overview: 'overview',
      site: 'site',
      cabinet: 'cabinet',
      structural: 'structural',
      foundation: 'foundation',
      finalization: 'finalization',
      review: 'review',
      submission: 'submission',
    };
    return stageMap[currentStage] || 'home';
  };

  return (
    <Paper sx={{ position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 1000 }} elevation={3} role="navigation" aria-label="Mobile navigation">
      <BottomNavigation value={getCurrentValue()} onChange={handleChange} showLabels>
        <BottomNavigationAction
          label="Projects"
          value="home"
          icon={<HomeIcon />}
          aria-label="View all projects"
        />
        <BottomNavigationAction
          label="Site"
          value="site"
          icon={<ExploreIcon />}
          aria-label="Site and environmental data"
        />
        <BottomNavigationAction
          label="Design"
          value="cabinet"
          icon={<AccountTreeIcon />}
          aria-label="Cabinet and structural design"
        />
        <BottomNavigationAction
          label="Review"
          value="review"
          icon={<AssessmentIcon />}
          aria-label="Project review"
        />
      </BottomNavigation>
    </Paper>
  );
}
