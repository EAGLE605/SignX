import { debounce } from './debounce';

export interface AutosaveOptions {
  delay?: number;
  onSave: () => void | Promise<void>;
}

export function useAutosave({ delay = 1000, onSave }: AutosaveOptions) {
  const debouncedSave = debounce(() => {
    void onSave();
  }, delay);

  return debouncedSave;
}
