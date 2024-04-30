import { render, screen, fireEvent } from '@testing-library/react';
import { Modal } from '../Modal';

describe('Modal', () => {
  it('closes on escape', () => {
    const onClose = vi.fn();
    render(<Modal open title="Test" onClose={onClose}>Content</Modal>);
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onClose).toHaveBeenCalled();
  });
});
