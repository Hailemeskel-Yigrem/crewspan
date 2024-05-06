import { describe, it, expect } from 'vitest';
import { formatDateTime, formatDate, isToday } from '../dates';

describe('dates', () => {
  it('formatDateTime handles ISO strings', () => {
    const result = formatDateTime('2024-06-15T14:30:00Z');
    expect(result).not.toBe('—');
  });

  it('formatDate returns dash for null', () => {
    expect(formatDate(null)).toBe('—');
  });
});
