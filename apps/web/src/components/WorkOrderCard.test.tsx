import { render, screen, fireEvent } from '@testing-library/react';
import { WorkOrderCard } from '../WorkOrderCard';

const wo = { id: '1', orderNumber: 'WO-001', title: 'Repair HVAC', status: 'in_progress', priority: 'high' };

describe('WorkOrderCard', () => {
  it('renders work order details', () => {
    render(<WorkOrderCard workOrder={wo} />);
    expect(screen.getByText('WO-001')).toBeInTheDocument();
    expect(screen.getByText('Repair HVAC')).toBeInTheDocument();
  });
});
