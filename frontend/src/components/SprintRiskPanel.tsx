import type { RiskTag, SprintRisk } from '../api/sprints';

const TAG_LABELS: Record<RiskTag, string> = {
  migrated: '🔁 Já migrou',
  stalled: '⏸️ Parado',
  blocked: '🚫 Bloqueado',
  behind_schedule: '⚠️ Atrasado',
};

export function SprintRiskPanel({ data }: { data: SprintRisk }) {
  const summary = (
    <p>
      <strong>{data.at_risk_count}</strong> de {data.total_items} itens em risco
      {data.days_remaining !== null && (
        <> · {data.days_remaining >= 0 ? `${data.days_remaining} dia(s) restante(s)` : 'sprint encerrada'}</>
      )}
      {data.awaiting_deploy_count > 0 && (
        <>
          {' · '}
          <strong>{data.awaiting_deploy_count}</strong> pronto(s), aguardando deploy
          {data.next_deploy_date && ` (próxima janela: ${new Date(data.next_deploy_date).toLocaleDateString('pt-BR')})`}
        </>
      )}
      {data.in_production_count > 0 && (
        <>
          {' · '}
          <strong>{data.in_production_count}</strong> já em produção
        </>
      )}
    </p>
  );

  if (data.items.length === 0) {
    return (
      <div>
        {summary}
        <p>Nenhum item em risco identificado nesta sprint.</p>
      </div>
    );
  }

  return (
    <div>
      {summary}
      <div style={{ overflowX: 'auto' }}>
        <table className="workload-table">
          <thead>
            <tr>
              <th>Issue</th>
              <th>Resumo</th>
              <th>Responsável</th>
              <th>Status</th>
              <th>Sinais</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((item) => (
              <tr key={item.issue_key}>
                <td>{item.issue_key}</td>
                <td>{item.summary}</td>
                <td>{item.assignee ?? '—'}</td>
                <td>{item.status}</td>
                <td>{item.tags.map((tag) => TAG_LABELS[tag]).join(' · ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
