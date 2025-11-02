import { useState } from 'react';
import { TextField, Button, Box } from '@mui/material';
import { useMutation } from '@tanstack/react-query';
import api from '../../lib/api';

interface SiteData {
  address: string;
  wind_speed_mph: number;
  snow_load_psf: number;
}

export default function SiteInfo({ onNext }: { onNext: (data: unknown) => void }) {
  const [address, setAddress] = useState('');
  const [windSpeed, setWindSpeed] = useState(90);
  const [snowLoad, setSnowLoad] = useState(25);

  const resolveMutation = useMutation({
    mutationFn: (data: SiteData) => api.post('/signage/site/resolve', data),
    onSuccess: (response) => onNext(response.data.result),
  });

  const handleSubmit = () => {
    resolveMutation.mutate({
      address,
      wind_speed_mph: windSpeed,
      snow_load_psf: snowLoad,
    });
  };

  return (
    <Box>
      <TextField
        fullWidth
        label="Site Address"
        value={address}
        onChange={(e) => setAddress(e.target.value)}
        margin="normal"
      />
      <TextField
        fullWidth
        label="Wind Speed (mph)"
        type="number"
        value={windSpeed}
        onChange={(e) => setWindSpeed(Number(e.target.value))}
        margin="normal"
      />
      <TextField
        fullWidth
        label="Snow Load (psf)"
        type="number"
        value={snowLoad}
        onChange={(e) => setSnowLoad(Number(e.target.value))}
        margin="normal"
      />
      <Button
        variant="contained"
        onClick={handleSubmit}
        disabled={resolveMutation.isPending}
      >
        {resolveMutation.isPending ? 'Loading...' : 'Next'}
      </Button>
    </Box>
  );
}

