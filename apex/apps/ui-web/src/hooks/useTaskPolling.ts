import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../api/client';
import { useToast } from '../components/Toast';
import type { TaskStatus } from '../types/envelope';

interface UseTaskPollingOptions {
  taskId: string | null;
  onComplete?: (result: unknown) => void;
  onError?: (error: string) => void;
  pollInterval?: number;
  maxAttempts?: number;
}

export function useTaskPolling({
  taskId,
  onComplete,
  onError,
  pollInterval = 2000,
  maxAttempts = 150, // 5 minutes max
}: UseTaskPollingOptions) {
  const [status, setStatus] = useState<TaskStatus | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const attemptsRef = useRef(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const { showToast } = useToast();

  const poll = useCallback(async () => {
    if (!taskId) return;

    try {
      const envelope = await api.getTaskStatus(taskId);
      if (envelope.result) {
        setStatus(envelope.result);
        attemptsRef.current += 1;

        if (envelope.result.status === 'completed') {
          setIsPolling(false);
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          onComplete?.(envelope.result.result);
          showToast('Task completed successfully', 'success');
        } else if (envelope.result.status === 'failed') {
          setIsPolling(false);
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          const errorMsg = envelope.result.error || 'Task failed';
          onError?.(errorMsg);
          showToast(errorMsg, 'error');
        } else if (attemptsRef.current >= maxAttempts) {
          setIsPolling(false);
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          onError?.('Task polling timeout');
          showToast('Task is taking longer than expected', 'warning');
        }
      }
    } catch (error) {
      setIsPolling(false);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      const errorMsg = error instanceof Error ? error.message : 'Failed to poll task status';
      onError?.(errorMsg);
      showToast(errorMsg, 'error');
    }
  }, [taskId, onComplete, onError, maxAttempts, showToast]);

  useEffect(() => {
    if (!taskId || isPolling) return;

    setIsPolling(true);
    attemptsRef.current = 0;
    poll(); // Initial poll

    intervalRef.current = setInterval(() => {
      poll();
    }, pollInterval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [taskId, pollInterval, poll, isPolling]);

  const stopPolling = useCallback(() => {
    setIsPolling(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  return {
    status,
    isPolling,
    progress: status?.progress ?? 0,
    stopPolling,
  };
}
