import { useQuery } from '@tanstack/react-query';
import { Button, Card, CardContent, Typography, Grid } from '@mui/material';
import api from '../lib/api';
import { useNavigate } from 'react-router-dom';
import type { Project } from '../types/api';

export default function ProjectList() {
  const navigate = useNavigate();
  const { data } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.get('/projects').then((res) => res.data.result || []),
  });

  return (
    <div>
      <Button variant="contained" onClick={() => navigate('/project/new')}>
        New Project
      </Button>
      <Grid container spacing={2} sx={{ mt: 2 }}>
        {data?.map((project: Project) => (
          <Grid item xs={12} md={4} key={project.id}>
            <Card
              onClick={() => navigate(`/project/${project.id}`)}
              sx={{ cursor: 'pointer' }}
            >
              <CardContent>
                <Typography variant="h6">{project.name}</Typography>
                <Typography color="text.secondary">{project.status}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </div>
  );
}

