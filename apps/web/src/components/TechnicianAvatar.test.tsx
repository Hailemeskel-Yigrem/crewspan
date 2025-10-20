import { render, screen } from '@testing-library/react';
import { TechnicianAvatar } from '../TechnicianAvatar';

describe('TechnicianAvatar', () => {
  it('shows initials', () => {
    render(<TechnicianAvatar name="Jane Doe" />);
    expect(screen.getByText('JD')).toBeInTheDocument();
  });
});
// history-note: evolutionary edit 41
