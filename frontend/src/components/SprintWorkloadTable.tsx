import type { WorkloadByStatus } from '../api/sprints';

function formatHours(seconds: number): string {
  if (!seconds) return '—';
  const hours = seconds / 3600;
  return `${hours % 1 === 0 ? hours : hours.toFixed(1)}h`;
}

export function SprintWorkloadTable({ data }: { data: WorkloadByStatus }) {
  if (data.rows.length === 0) {
    return <p>Nenhuma issue com responsável atribuído nesta sprint.</p>;
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="workload-table">
        <thead>
          <tr>
            <th>Colaborador</th>
            {data.statuses.map((status) => (
              <th key={status}>{status}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.rows.map((row) => (
            <tr key={row.person}>
              <td>{row.person}</td>
              {data.statuses.map((status) => {
                const cell = row.cells[status];
                return (
                  <td key={status}>
                    {cell ? (
                      <>
                        {cell.count} · {formatHours(cell.seconds)}
                      </>
                    ) : (
                      '—'
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
