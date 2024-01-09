import { FormEvent, useState } from 'react';
import { FormField } from '../components/FormField';
import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../hooks/useAuth';

export function SettingsPage() {
  const { user } = useAuth();
  const [timezone, setTimezone] = useState('UTC');
  const [notifications, setNotifications] = useState({ email: true, sms: false, dispatch: true });
  const [saved, setSaved] = useState(false);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="page">
      <PageHeader title="Settings" subtitle="Tenant preferences and notification routing" />
      <form onSubmit={handleSubmit} className="settings-form">
        <section className="settings-section">
          <h2>Tenant</h2>
          <FormField label="Tenant ID" htmlFor="set-tenant"><input id="set-tenant" value={user?.tenantId ?? ''} readOnly /></FormField>
          <FormField label="Timezone" htmlFor="set-tz"><select id="set-tz" value={timezone} onChange={(e) => setTimezone(e.target.value)}>
            <option value="UTC">UTC</option><option value="America/New_York">Eastern</option><option value="America/Chicago">Central</option><option value="America/Los_Angeles">Pacific</option>
          </select></FormField>
        </section>
        <section className="settings-section">
          <h2>Notifications</h2>
          <label><input type="checkbox" checked={notifications.email} onChange={(e) => setNotifications({ ...notifications, email: e.target.checked })} /> Email alerts</label>
          <label><input type="checkbox" checked={notifications.sms} onChange={(e) => setNotifications({ ...notifications, sms: e.target.checked })} /> SMS alerts</label>
          <label><input type="checkbox" checked={notifications.dispatch} onChange={(e) => setNotifications({ ...notifications, dispatch: e.target.checked })} /> Dispatch notifications</label>
        </section>
        <button type="submit" className="btn btn-primary">Save preferences</button>
        {saved ? <span style={{ color: 'var(--color-success)', marginLeft: '1rem' }}>Saved</span> : null}
      </form>
      <style>{`.settings-form { max-width: 560px; display: flex; flex-direction: column; gap: 1.5rem; } .settings-section { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 1.25rem; display: flex; flex-direction: column; gap: 0.75rem; } .settings-section h2 { margin: 0 0 0.5rem; font-size: 1rem; }`}</style>
    </div>
  );
}
