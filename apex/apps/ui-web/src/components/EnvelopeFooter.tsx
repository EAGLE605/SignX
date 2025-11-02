import { Box, Typography, Paper, Tooltip } from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import type { ResponseEnvelope } from '../types/envelope';

interface EnvelopeFooterProps {
  envelope?: ResponseEnvelope<unknown> | null;
}

export default function EnvelopeFooter({ envelope }: EnvelopeFooterProps) {
  if (!envelope) return null;

  const constantsVersion = envelope.trace?.constants_version;
  const gitSha = envelope.trace?.code_version?.git_sha;
  const buildId = envelope.trace?.code_version?.build_id;

  return (
    <Paper
      sx={{
        p: 1,
        mt: 2,
        bgcolor: 'background.default',
        borderTop: 1,
        borderColor: 'divider',
      }}
      elevation={0}
    >
      <Box display="flex" alignItems="center" gap={2} justifyContent="flex-end">
        {constantsVersion && (
          <Tooltip title="Constants version used in calculations">
            <Box display="flex" alignItems="center" gap={0.5}>
              <InfoIcon fontSize="small" color="action" />
              <Typography variant="caption" color="text.secondary">
                Constants: {constantsVersion}
              </Typography>
            </Box>
          </Tooltip>
        )}
        {gitSha && (
          <Tooltip title="Code version">
            <Box display="flex" alignItems="center" gap={0.5}>
              <InfoIcon fontSize="small" color="action" />
              <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                {gitSha.substring(0, 7)}
                {gitSha.length > 7 ? '...' : ''}
              </Typography>
            </Box>
          </Tooltip>
        )}
        {buildId && (
          <Tooltip title="Build ID">
            <Typography variant="caption" color="text.secondary">
              Build: {buildId}
            </Typography>
          </Tooltip>
        )}
      </Box>
    </Paper>
  );
}
