import { render, screen, fireEvent } from '@testing-library/react';
import { ConfirmDialog } from '../ConfirmDialog';

describe('ConfirmDialog', () => {
  it('calls onConfirm', () => {
    const onConfirm = vi.fn();
    render(<ConfirmDialog open title="Delete?" message="Sure?" onConfirm={onConfirm} onCancel={() => {}} />);
    fireEvent.click(screen.getByText('Confirm'));
    expect(onConfirm).toHaveBeenCalled();
  });
});
