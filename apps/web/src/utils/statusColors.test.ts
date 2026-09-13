import { describe, it, expect } from 'vitest';
import { statusColor, priorityWeight } from './statusColors';

describe('statusColors', () => {
  it('returns color for known status', () => {
    expect(statusColor('completed')).toBe('#14b8a6');
  });

  it('priorityWeight ranks critical highest', () => {
    expect(priorityWeight('critical')).toBeGreaterThan(priorityWeight('low'));
  });
});
