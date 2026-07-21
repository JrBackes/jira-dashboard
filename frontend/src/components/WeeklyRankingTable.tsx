import type { WeeklyTimeRanking } from '../api/people';

function formatHours(seconds: number): string {
  const hours = seconds / 3600;
  return `${hours % 1 === 0 ? hours : hours.toFixed(1)}h`;
}

export function WeeklyRankingTable({ data }: { data: WeeklyTimeRanking }) {
  const formattedRange = `${new Date(data.week_start).toLocaleDateString('pt-BR')} a ${new Date(data.week_end).toLocaleDateString('pt-BR')}`;

  if (data.ranking.length === 0) {
    return <p>Nenhum apontamento de tempo registrado na semana de {formattedRange}.</p>;
  }

  return (
    <div>
      <p>
        Semana de {formattedRange} · esperado por pessoa: <strong>{formatHours(data.expected_seconds)}</strong> (5 dias × 6h)
      </p>
      <div style={{ overflowX: 'auto' }}>
        <table className="workload-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Colaborador</th>
              <th>Tempo registrado</th>
              <th>% do esperado</th>
            </tr>
          </thead>
          <tbody>
            {data.ranking.map((row, index) => (
              <tr key={row.person}>
                <td>{index + 1}</td>
                <td>{row.person}</td>
                <td>{formatHours(row.seconds)}</td>
                <td>{row.percent_of_expected}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
