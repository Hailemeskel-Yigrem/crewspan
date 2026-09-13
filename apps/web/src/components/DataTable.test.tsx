import { render, screen, fireEvent } from '@testing-library/react';
import { DataTable } from './DataTable';

const data = [{ id: '1', name: 'Alpha' }, { id: '2', name: 'Beta' }];
const columns = [
  { key: 'name', header: 'Name', render: (r: { name: string }) => r.name },
];

describe('DataTable', () => {
  it('renders rows', () => {
    render(<DataTable columns={columns} data={data} keyExtractor={(r) => r.id} />);
    expect(screen.getByText('Alpha')).toBeInTheDocument();
    expect(screen.getByText('Beta')).toBeInTheDocument();
  });

  it('calls onRowClick', () => {
    const onClick = vi.fn();
    render(<DataTable columns={columns} data={data} keyExtractor={(r) => r.id} onRowClick={onClick} />);
    fireEvent.click(screen.getByText('Alpha'));
    expect(onClick).toHaveBeenCalledWith(data[0]);
  });
});
