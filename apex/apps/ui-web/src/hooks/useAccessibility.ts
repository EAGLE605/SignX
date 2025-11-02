/**
 * Accessibility utilities and hooks
 */

import { useEffect } from 'react';

export function useAnnounce(message: string, priority: 'polite' | 'assertive' = 'polite') {
  useEffect(() => {
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.style.cssText = 'position: absolute; left: -10000px; width: 1px; height: 1px; overflow: hidden;';
    document.body.appendChild(announcement);

    announcement.textContent = message;

    return () => {
      document.body.removeChild(announcement);
    };
  }, [message, priority]);
}

export function useFocusManagement(ref: React.RefObject<HTMLElement>, condition: boolean) {
  useEffect(() => {
    if (condition && ref.current) {
      ref.current.focus();
    }
  }, [condition, ref]);
}

export function useKeyboardShortcuts(
  shortcuts: Record<string, (e: KeyboardEvent) => void>,
) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const key = e.key.toLowerCase();
      const modifier = e.ctrlKey || e.metaKey ? 'ctrl+' : e.shiftKey ? 'shift+' : '';
      const shortcut = `${modifier}${key}`;

      if (shortcuts[shortcut] || shortcuts[key]) {
        const handler = shortcuts[shortcut] || shortcuts[key];
        e.preventDefault();
        handler(e);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);
}
