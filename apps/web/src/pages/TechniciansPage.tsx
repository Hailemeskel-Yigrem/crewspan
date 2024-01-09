import { useEffect, useState } from 'react';
import { DataTable, type Column } from '../components/DataTable';
import { PageHeader } from '../components/PageHeader';
import { StatusBadge } from '../components/StatusBadge';
import { TechnicianAvatar } from '../components/TechnicianAvatar';
import { technicianApi } from '../api/technician';
import type { Technician } from '../types/technician';

export function TechniciansPage() {
  const [techs, setTechs] = useState<Technician[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void technicianApi.list({ pageSize: 50 }).then((r) => { setTechs(r.data); setLoading(false); });
  }, []);

  const columns: Column<Technician>[] = [
    { key: 'avatar', header: '', render: (r) => <TechnicianAvatar name={r.employeeId} status={r.status} /> },
    { key: 'employeeId', header: 'Employee ID', render: (r) => r.employeeId },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
    { key: 'hours', header: 'Max Hours', render: (r) => String(r.maxDailyHours) },
  ];

  return (
    <div className="page">
      <PageHeader title="Technicians" subtitle="Field technician roster and availability" />
      {!loading ? <DataTable columns={columns} data={techs} keyExtractor={(r) => r.id} /> : null}
    </div>
  );
}
