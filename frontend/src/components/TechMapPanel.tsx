import type { TechMapGroup } from '../api/techMap';

export function TechMapPanel({ groups }: { groups: TechMapGroup[] }) {
  if (groups.length === 0) {
    return <p>Nenhum item na sprint atual.</p>;
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="workload-table">
        <thead>
          <tr>
            <th>Epic</th>
            <th>Issues na sprint</th>
            <th>Frente</th>
            <th>Status (planilha)</th>
            <th>Score ICE</th>
            <th>Entrega prevista</th>
          </tr>
        </thead>
        <tbody>
          {groups.map((group) => (
            <tr key={group.epic_key ?? 'sem-epic'}>
              <td>
                {group.epic_key ? (
                  <>{group.epic_key} — {group.epic_summary}</>
                ) : (
                  <em>Sem Epic vinculado</em>
                )}
              </td>
              <td>{group.issue_count}</td>
              {group.tech_map ? (
                <>
                  <td>{group.tech_map.frente ?? '—'}</td>
                  <td>{group.tech_map.status ?? '—'}</td>
                  <td>{group.tech_map.ice_score ?? '—'}</td>
                  <td>{group.tech_map.entrega ?? '—'}</td>
                </>
              ) : (
                <td colSpan={4}>
                  <em>{group.epic_key ? 'Sem vínculo no Mapa de Tecnologia (coluna "Epic Jira")' : '—'}</em>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
