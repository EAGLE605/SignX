import { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  Collapse,
} from '@mui/material';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';
import { api, APIError } from '../api/client';
import { useToast } from './Toast';
import { parseEnvelope } from '../utils/envelope';
import type { ProjectEvent } from '../types/envelope';

interface ProjectHistoryProps {
  projectId: string;
}

export default function ProjectHistory({ projectId }: ProjectHistoryProps) {
  const [events, setEvents] = useState<ProjectEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null);
  const { showToast } = useToast();

  const loadEvents = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.getProjectEvents(projectId);
      const parsed = parseEnvelope(response);
      if (parsed.data) {
        setEvents(parsed.data.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()));
      }
    } catch (error) {
      const message =
        error instanceof APIError ? error.message : error instanceof Error ? error.message : 'Failed to load events';
      showToast(message, 'error');
    } finally {
      setLoading(false);
    }
  }, [projectId, showToast]);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  const getEventColor = (eventType: string): 'primary' | 'info' | 'success' | 'error' | 'default' => {
    if (eventType.includes('created')) return 'primary';
    if (eventType.includes('updated')) return 'info';
    if (eventType.includes('submitted')) return 'success';
    if (eventType.includes('error')) return 'error';
    return 'default';
  };

  const toggleEvent = (eventId: string) => {
    setExpandedEventId(expandedEventId === eventId ? null : eventId);
  };

  if (loading) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography>Loading project history...</Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Project History & Timeline
      </Typography>

      {events.length === 0 ? (
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          No events yet.
        </Typography>
      ) : (
        <List sx={{ mt: 2 }}>
          {events.map((event) => (
            <ListItem
              key={event.id}
              sx={{
                flexDirection: 'column',
                alignItems: 'stretch',
                borderLeft: '2px solid',
                borderColor: event.event_type.includes('error') ? 'error.main' : 'primary.main',
                pl: 2,
                mb: 1,
              }}
            >
              <Box display="flex" alignItems="center" justifyContent="space-between" width="100%">
                <Box display="flex" alignItems="center" gap={1}>
                  <Typography variant="subtitle2">{event.event_type}</Typography>
                  <Chip label={event.event_type} size="small" color={getEventColor(event.event_type)} />
                </Box>
                <Typography variant="caption" color="text.secondary">
                  {new Date(event.created_at).toLocaleString()}
                </Typography>
              </Box>
              {Object.keys(event.payload || {}).length > 0 && (
                <Box sx={{ width: '100%', mt: 1 }}>
                  <Accordion>
                    <AccordionSummary
                      expandIcon={expandedEventId === event.id ? <ExpandLess /> : <ExpandMore />}
                      onClick={() => toggleEvent(event.id)}
                    >
                      <Typography variant="caption">View Details</Typography>
                    </AccordionSummary>
                    <Collapse in={expandedEventId === event.id}>
                      <AccordionDetails>
                        <Box
                          component="pre"
                          sx={{
                            bgcolor: 'background.default',
                            p: 1,
                            borderRadius: 1,
                            fontSize: '0.75rem',
                            overflow: 'auto',
                            maxHeight: 200,
                          }}
                        >
                          {JSON.stringify(event.payload, null, 2)}
                        </Box>
                      </AccordionDetails>
                    </Collapse>
                  </Accordion>
                </Box>
              )}
            </ListItem>
          ))}
        </List>
      )}
    </Paper>
  );
}
