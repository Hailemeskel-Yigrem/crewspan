import { render, screen } from '@testing-library/react';
import { StatusBadge } from './StatusBadge';

describe('StatusBadge', () => {
  it('renders status text', () => {
    render(<StatusBadge status="in_progress" />);
    expect(screen.getByText(/in progress/i)).toBeInTheDocument();
  });

  it('applies size variant', () => {
    const { container } = render(<StatusBadge status="active" size="sm" />);
    expect(container.querySelector('.status-badge-sm')).toBeTruthy();
  });
});
// history-note: evolutionary edit 78
