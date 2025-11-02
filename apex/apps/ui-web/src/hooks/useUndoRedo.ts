import { useState, useCallback, useRef } from 'react';

interface HistoryItem<T> {
  state: T;
  timestamp: number;
}

export function useUndoRedo<T>(initialState: T, maxHistory = 50) {
  const [currentState, setCurrentState] = useState<T>(initialState);
  const historyRef = useRef<HistoryItem<T>[]>([{ state: initialState, timestamp: Date.now() }]);
  const historyIndexRef = useRef(0);

  const pushState = useCallback(
    (newState: T) => {
      // Remove any "future" history if we're not at the end
      historyRef.current = historyRef.current.slice(0, historyIndexRef.current + 1);

      // Add new state
      historyRef.current.push({ state: newState, timestamp: Date.now() });

      // Limit history size
      if (historyRef.current.length > maxHistory) {
        historyRef.current.shift();
      } else {
        historyIndexRef.current += 1;
      }

      setCurrentState(newState);
    },
    [maxHistory],
  );

  const undo = useCallback(() => {
    if (historyIndexRef.current > 0) {
      historyIndexRef.current -= 1;
      const prevState = historyRef.current[historyIndexRef.current].state;
      setCurrentState(prevState);
      return true;
    }
    return false;
  }, []);

  const redo = useCallback(() => {
    if (historyIndexRef.current < historyRef.current.length - 1) {
      historyIndexRef.current += 1;
      const nextState = historyRef.current[historyIndexRef.current].state;
      setCurrentState(nextState);
      return true;
    }
    return false;
  }, []);

  const canUndo = historyIndexRef.current > 0;
  const canRedo = historyIndexRef.current < historyRef.current.length - 1;

  return {
    state: currentState,
    setState: pushState,
    undo,
    redo,
    canUndo,
    canRedo,
    historyLength: historyRef.current.length,
  };
}
