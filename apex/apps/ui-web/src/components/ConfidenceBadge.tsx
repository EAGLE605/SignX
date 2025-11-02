import { Chip, Tooltip } from '@mui/material';
import { getConfidenceColor, getConfidenceLevel, type ConfidenceLevel } from '../types/envelope';

interface ConfidenceBadgeProps {
  confidence: number;
  showLabel?: boolean;
  size?: 'small' | 'medium';
}

export default function ConfidenceBadge({ confidence, showLabel = true, size = 'small' }: ConfidenceBadgeProps) {
  const level: ConfidenceLevel = getConfidenceLevel(confidence);
  const color = getConfidenceColor(confidence);
  const label = `${Math.round(confidence * 100)}%`;

  const getLevelLabel = () => {
    switch (level) {
      case 'high':
        return 'High Confidence';
      case 'medium':
        return 'Medium Confidence';
      case 'low':
        return 'Low Confidence - Review Required';
    }
  };

  return (
    <Tooltip title={`${getLevelLabel()}: ${confidence.toFixed(2)}`}>
      <Chip
        label={showLabel ? label : ''}
        size={size}
        sx={{
          bgcolor: color,
          color: 'white',
          fontWeight: 'bold',
          '& .MuiChip-label': {
            px: 1.5,
          },
        }}
      />
    </Tooltip>
  );
}
