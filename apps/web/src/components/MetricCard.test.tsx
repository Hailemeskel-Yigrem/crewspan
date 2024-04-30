import { render, screen } from '@testing-library/react';
import { MetricCard } from '../MetricCard';

describe('MetricCard', () => {
  it('displays value and label', () => {
    render(<MetricCard label="Open Orders" value={42} />);
    expect(screen.getByText('Open Orders')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
  });
});
