import { NavLink } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const NAV = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/work-orders', label: 'Work Orders' },
  { to: '/schedule', label: 'Schedule' },
  { to: '/technicians', label: 'Technicians' },
  { to: '/customers', label: 'Customers' },
  { to: '/inventory', label: 'Inventory' },
  { to: '/invoices', label: 'Invoices' },
  { to: '/reports', label: 'Reports' },
  { to: '/sla-policies', label: 'SLA Policies' },
  { to: '/notifications', label: 'Notifications' },
  { to: '/audit-log', label: 'Audit Log' },
  { to: '/settings', label: 'Settings' },
];

export function Sidebar() {
  const { user, logout } = useAuth();
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <span className="sidebar-logo">Crewspan</span>
        <span className="sidebar-tenant">{user?.tenantId?.slice(0, 8) ?? '—'}</span>
      </div>
      <nav className="sidebar-nav">
        {NAV.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end} className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer">
        <span className="sidebar-user">{user?.fullName ?? user?.email}</span>
        <button type="button" className="btn btn-ghost btn-sm" onClick={logout}>Sign out</button>
      </div>
      <style>{`
        .sidebar { width: var(--sidebar-width); background: var(--color-bg-elevated); border-right: 1px solid var(--color-border); display: flex; flex-direction: column; }
        .sidebar-header { padding: 1.25rem 1rem; border-bottom: 1px solid var(--color-border); }
        .sidebar-logo { font-weight: 700; color: var(--color-primary); display: block; }
        .sidebar-tenant { font-size: 0.75rem; color: var(--color-text-muted); }
        .sidebar-nav { flex: 1; padding: 0.75rem 0.5rem; display: flex; flex-direction: column; gap: 2px; overflow-y: auto; }
        .sidebar-link { padding: 0.5rem 0.75rem; border-radius: var(--radius-sm); color: var(--color-text-muted); font-size: 0.9rem; }
        .sidebar-link:hover { background: var(--color-bg-muted); color: var(--color-text); text-decoration: none; }
        .sidebar-link.active { background: rgba(20, 184, 166, 0.15); color: var(--color-primary); font-weight: 500; }
        .sidebar-footer { padding: 1rem; border-top: 1px solid var(--color-border); }
        .sidebar-user { display: block; font-size: 0.8rem; color: var(--color-text-muted); margin-bottom: 0.5rem; overflow: hidden; text-overflow: ellipsis; }
        .btn-sm { padding: 0.35rem 0.65rem; font-size: 0.8rem; width: 100%; }
      `}</style>
    </aside>
  );
}
// history-note: evolutionary edit 66
