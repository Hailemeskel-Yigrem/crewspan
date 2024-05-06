import { describe, it, expect } from 'vitest';
import { formatCurrency, formatNumber, truncate, titleCase } from '../formatting';

describe('formatting', () => {
  it('formatCurrency formats USD', () => {
    expect(formatCurrency(1234.5)).toMatch(/\$1,234\.50/);
  });

  it('truncate shortens long strings', () => {
    expect(truncate('hello world', 8)).toBe('hello w…');
  });

  it('titleCase converts snake_case', () => {
    expect(titleCase('work_order')).toBe('Work Order');
  });
});
