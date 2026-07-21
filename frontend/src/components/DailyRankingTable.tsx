import type { DailyTimeBreakdown } from '../api/people';

function formatHours(seconds: number): string {
  const hours = seconds / 3600;
  return `${hours % 1 === 0 ? hours : hours.toFixed(1)}h`;
}

function formatDayLabel(iso: string): string {
  const parsed = new Date(`${iso}T00:00:00`);
  const weekday = parsed.toLocaleDateString('pt-BR', { weekday: 'short' }).replace('.', '');
  const dayMonth = parsed.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
  return `${weekday} ${dayMonth}`;
}

export function DailyRankingTable({ data }: { data: DailyTimeBreakdown }) {
  if (data.rows.length === 0) {
    return <p>Nenhum apontamento de tempo registrado nos dias já decorridos desta semana.</p>;
  }

  return (
    <div>
      <p style={{ fontSize: '0.85rem', color: '#64748b' }}>
        Esperado por dia: <strong>{formatHours(data.expected_per_day_seconds)}</strong> · ↑ acima, ↓ abaixo do esperado naquele dia
      </p>
      <div style={{ overflowX: 'auto' }}>
        <table className="workload-table">
          <thead>
            <tr>
              <th>Colaborador</th>
              {data.days.map((day) => (
                <th key={day}>{formatDayLabel(day)}</th>
              ))}
              <th>Acumulado</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row) => (
              <tr key={row.person}>
                <td>{row.person}</td>
                {data.days.map((day) => {
                  const seconds = row.cells[day] ?? 0;
                  if (seconds === 0) return <td key={day}>—</td>;
                  const delta = seconds - data.expected_per_day_seconds;
                  const arrow = delta > 0 ? ' ↑' : delta < 0 ? ' ↓' : '';
                  return <td key={day}>{formatHours(seconds)}{arrow}</td>;
                })}
                <td>{formatHours(row.total_seconds)} de {formatHours(row.expected_total_seconds)} esperado</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
