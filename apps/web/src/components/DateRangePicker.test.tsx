import { render, screen, fireEvent } from '@testing-library/react';
import { DateRangePicker } from './DateRangePicker';

describe('DateRangePicker', () => {
  it('updates range on change', () => {
    const onChange = vi.fn();
    render(<DateRangePicker value={{ start: '', end: '' }} onChange={onChange} />);
    fireEvent.change(screen.getByLabelText(/start/i), { target: { value: '2024-01-01' } });
    expect(onChange).toHaveBeenCalledWith({ start: '2024-01-01', end: '' });
  });
});
