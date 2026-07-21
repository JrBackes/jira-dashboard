import type { BlockedItem } from '../api/sprints';

export function BlockedItemsPanel({ items }: { items: BlockedItem[] }) {
  if (items.length === 0) {
    return <p>Nenhum item bloqueado nesta sprint.</p>;
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="workload-table">
        <thead>
          <tr>
            <th>Issue</th>
            <th>Resumo</th>
            <th>Responsável</th>
            <th>Bloqueado desde</th>
            <th>Motivo do bloqueio</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.issue_key}>
              <td>{item.issue_key}</td>
              <td>{item.summary}</td>
              <td>{item.assignee ?? '—'}</td>
              <td>
                {new Date(item.blocked_since).toLocaleDateString('pt-BR')} ({item.days_blocked} dia
                {item.days_blocked === 1 ? '' : 's'})
              </td>
              <td>
                {item.blockers.length === 0 ? (
                  <em>Sem vínculo registrado no Jira</em>
                ) : (
                  <ul style={{ margin: 0, paddingLeft: '1.2rem' }}>
                    {item.blockers.map((blocker) => (
                      <li key={blocker.issue_key}>
                        {blocker.issue_key} — {blocker.summary} ({blocker.status ?? 'status desconhecido'})
                      </li>
                    ))}
                  </ul>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
