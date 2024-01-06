import { useCallback, useEffect, useState } from 'react';
import { DateRangePicker, type DateRange } from '../components/DateRangePicker';
import { FormField } from '../components/FormField';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { Modal } from '../components/Modal';
import { PageHeader } from '../components/PageHeader';
import { TechnicianAvatar } from '../components/TechnicianAvatar';
import { scheduleApi } from '../api/schedule';
import type { Schedule } from '../types/schedule';
import { formatDateTime } from '../utils/dates';

export function SchedulePage() {
  const [events, setEvents] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [range, setRange] = useState<DateRange>({ start: new Date().toISOString().slice(0, 10), end: '' });
  const [techFilter, setTechFilter] = useState('');
  const [selected, setSelected] = useState<Schedule | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await scheduleApi.list({ pageSize: 100 });
      setEvents(res.data.filter((e) => !techFilter || e.technicianId.includes(techFilter)));
    } finally { setLoading(false); }
  }, [techFilter]);

  useEffect(() => { void load(); }, [load]);

  return (
    <div className="page">
      <PageHeader title="Schedule" subtitle="Technician availability and appointments" />
      <div className="toolbar">
        <FormField label="Technician ID" htmlFor="sched-tech"><input id="sched-tech" value={techFilter} onChange={(e) => setTechFilter(e.target.value)} placeholder="Filter by technician..." /></FormField>
        <DateRangePicker value={range} onChange={setRange} label="View range" />
      </div>
      {loading ? <LoadingSpinner /> : (
        <div className="schedule-grid">
          {events.map((ev) => (
            <button key={ev.id} type="button" className="schedule-block" onClick={() => setSelected(ev)}>
              <TechnicianAvatar name={ev.title} size={32} />
              <div><strong>{ev.title}</strong><br /><small>{formatDateTime(ev.startsAt)} — {formatDateTime(ev.endsAt)}</small></div>
              {ev.isLocked ? <span className="lock-badge">🔒</span> : null}
            </button>
          ))}
        </div>
      )}
      <Modal open={Boolean(selected)} title="Schedule Event" onClose={() => setSelected(null)}>
        {selected ? <dl className="detail-grid"><dt>Type</dt><dd>{selected.eventType}</dd><dt>Notes</dt><dd>{selected.notes ?? '—'}</dd></dl> : null}
      </Modal>
      <style>{`.schedule-grid { display: flex; flex-direction: column; gap: 0.5rem; } .schedule-block { display: flex; align-items: center; gap: 1rem; padding: 0.75rem 1rem; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-md); cursor: pointer; text-align: left; width: 100%; color: inherit; } .schedule-block:hover { border-color: var(--color-primary); }`}</style>
    </div>
  );
}
