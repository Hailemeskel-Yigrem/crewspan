import { ReactNode } from 'react';

export interface Column<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  width?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string;
  onRowClick?: (row: T) => void;
  pagination?: { page: number; pageSize: number; totalPages: number; onPageChange: (p: number) => void };
  emptyMessage?: string;
}

export function DataTable<T>({ columns, data, keyExtractor, onRowClick, pagination, emptyMessage }: DataTableProps<T>) {
  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <thead>
          <tr>{columns.map((c) => <th key={c.key} style={{ width: c.width }}>{c.header}</th>)}</tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr><td colSpan={columns.length} className="data-table-empty">{emptyMessage ?? 'No records'}</td></tr>
          ) : data.map((row) => (
            <tr key={keyExtractor(row)} onClick={() => onRowClick?.(row)} className={onRowClick ? 'clickable' : undefined}>
              {columns.map((c) => <td key={c.key}>{c.render(row)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
      {pagination ? (
        <div className="data-table-pagination">
          <button type="button" className="btn btn-ghost btn-sm" disabled={pagination.page <= 1} onClick={() => pagination.onPageChange(pagination.page - 1)}>Prev</button>
          <span>Page {pagination.page} of {pagination.totalPages}</span>
          <button type="button" className="btn btn-ghost btn-sm" disabled={pagination.page >= pagination.totalPages} onClick={() => pagination.onPageChange(pagination.page + 1)}>Next</button>
        </div>
      ) : null}
      <style>{`
        .data-table-wrap { border: 1px solid var(--color-border); border-radius: var(--radius-md); overflow: hidden; background: var(--color-surface); }
        .data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
        .data-table th, .data-table td { padding: 0.65rem 1rem; text-align: left; border-bottom: 1px solid var(--color-border); }
        .data-table th { background: var(--color-bg-muted); color: var(--color-text-muted); font-weight: 500; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; }
        .data-table tr.clickable { cursor: pointer; }
        .data-table tr.clickable:hover td { background: rgba(20, 184, 166, 0.08); }
        .data-table-empty { text-align: center; color: var(--color-text-muted); padding: 2rem !important; }
        .data-table-pagination { display: flex; align-items: center; justify-content: flex-end; gap: 1rem; padding: 0.75rem 1rem; border-top: 1px solid var(--color-border); font-size: 0.875rem; color: var(--color-text-muted); }
      `}</style>
    </div>
  );
}
