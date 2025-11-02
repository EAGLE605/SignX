import { useState, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Chip,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import DeleteIcon from '@mui/icons-material/Delete';
import VerifiedIcon from '@mui/icons-material/Verified';
import { api, APIError } from '../api/client';
import { useToast } from './Toast';
import type { FileAttachment } from '../types/envelope';
import { sha256_digest } from '../utils/crypto';

interface FileUploadProps {
  projectId: string;
  onUploadComplete?: (files: FileAttachment[]) => void;
}

export default function FileUpload({ projectId, onUploadComplete: _onUploadComplete }: FileUploadProps) {
  const [files, setFiles] = useState<FileAttachment[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { showToast } = useToast();

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = event.target.files;
    if (!selectedFiles || selectedFiles.length === 0) return;

    setUploading(true);
    setError(null);

    try {
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        const fileId = `${Date.now()}-${i}`;

        try {
          // Step 1: Get presigned URL
          const presignResponse = await api.getPresignedUploadUrl(
            projectId,
            file.name,
            file.type || 'application/octet-stream',
          );

          if (!presignResponse.result) {
            throw new Error('Failed to get presigned URL');
          }

          // Step 2: Compute SHA256
          const arrayBuffer = await file.arrayBuffer();
          const fileHash = await sha256_digest(arrayBuffer);

          // Step 3: Upload to MinIO with progress
          const xhr = new XMLHttpRequest();
          await new Promise<void>((resolve, reject) => {
            xhr.upload.addEventListener('progress', (e) => {
              if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                setUploadProgress((prev) => ({ ...prev, [fileId]: percent }));
              }
            });

            xhr.addEventListener('load', () => {
              if (xhr.status >= 200 && xhr.status < 300) {
                resolve();
              } else {
                reject(new Error(`Upload failed: ${xhr.statusText}`));
              }
            });

            xhr.addEventListener('error', () => reject(new Error('Upload network error')));
            if (!presignResponse.result) {
              reject(new Error('No presigned URL available'));
              return;
            }
            xhr.open('PUT', presignResponse.result.url);
            xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');
            xhr.send(arrayBuffer);
          });

          // Step 4: Attach file to project
          const attachResponse = await api.attachFile(
            projectId,
            presignResponse.result.key,
            fileHash,
            file.name,
            file.size,
            file.type || 'application/octet-stream',
          );

          if (attachResponse.result) {
            setFiles((prev) => [...prev, attachResponse.result!]);
            setUploadProgress((prev) => {
              const updated = { ...prev };
              delete updated[fileId];
              return updated;
            });
            showToast(`File "${file.name}" uploaded successfully`, 'success');
          }
        } catch (fileError) {
          const message =
            fileError instanceof APIError
              ? fileError.message
              : fileError instanceof Error
              ? fileError.message
              : `Failed to upload ${file.name}`;
          showToast(message, 'error');
          setUploadProgress((prev) => {
            const updated = { ...prev };
            delete updated[fileId];
            return updated;
          });
        }
      }

      // Files already added to state above
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Upload failed';
      setError(message);
      showToast(message, 'error');
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleRemove = async (key: string) => {
    // TODO: Implement file deletion endpoint
    setFiles((prev) => prev.filter((f) => f.key !== key));
    showToast('File removed', 'info');
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        File Upload
      </Typography>

      <Box sx={{ mt: 2 }}>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          style={{ display: 'none' }}
          onChange={handleFileSelect}
          accept=".pdf,.dwg,.dxf,.jpg,.jpeg,.png"
          capture="environment"
          aria-label="Select files to upload"
        />
        <Button
          variant="contained"
          component="label"
          startIcon={<CloudUploadIcon />}
          disabled={uploading}
        >
          {uploading ? 'Uploading...' : 'Select Files'}
          <input type="file" multiple hidden onChange={handleFileSelect} />
        </Button>
      </Box>

      {Object.keys(uploadProgress).length > 0 && (
        <Box sx={{ mt: 2 }}>
          {Object.entries(uploadProgress).map(([fileId, progress]) => (
            <Box key={fileId} sx={{ mb: 1 }}>
              <Typography variant="caption">Uploading... {progress}%</Typography>
              <LinearProgress variant="determinate" value={progress} sx={{ mt: 0.5 }} />
            </Box>
          ))}
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      {files.length > 0 && (
        <List sx={{ mt: 2 }}>
          {files.map((file) => (
            <ListItem
              key={file.key}
              secondaryAction={
                <Box display="flex" alignItems="center" gap={1}>
                  {file.sha256 && (
                    <Chip
                      icon={<VerifiedIcon />}
                      label="Verified"
                      size="small"
                      color="success"
                      sx={{ height: 24 }}
                    />
                  )}
                  <IconButton edge="end" onClick={() => handleRemove(file.key)} size="small">
                    <DeleteIcon />
                  </IconButton>
                </Box>
              }
            >
              <ListItemText
                primary={file.filename}
                secondary={
                  <Box>
                    <Typography variant="caption" component="span">
                      {formatFileSize(file.size)}
                    </Typography>
                    {file.sha256 && (
                      <Typography variant="caption" component="span" sx={{ ml: 2, fontFamily: 'monospace' }}>
                        SHA256: {file.sha256.substring(0, 8)}...
                      </Typography>
                    )}
                  </Box>
                }
              />
            </ListItem>
          ))}
        </List>
      )}
    </Paper>
  );
}