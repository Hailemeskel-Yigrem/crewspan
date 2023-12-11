import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { ToastContainer } from './Toast';

export function Layout() {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="app-main"><Outlet /></main>
      <ToastContainer />
      <style>{`
        .app-layout { display: flex; min-height: 100vh; }
        .app-main { flex: 1; overflow: auto; background: var(--color-bg); }
      `}</style>
    </div>
  );
}
