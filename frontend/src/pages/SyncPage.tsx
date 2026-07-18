import { useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchSyncStatus, triggerSync } from '../api/sync';

function formatDateTime(iso: string): string {
  return new Date(`${iso}Z`).toLocaleString('pt-BR');
}

export function SyncPage() {
  const queryClient = useQueryClient();

  const { data: statuses } = useQuery({
    queryKey: ['sync-status'],
    queryFn: fetchSyncStatus,
    refetchInterval: (query) => (query.state.data?.some((s) => s.last_run?.status === 'running') ? 2000 : false),
  });

  const isAnyRunning = statuses?.some((s) => s.last_run?.status === 'running') ?? false;

  const handleClick = async () => {
    await triggerSync();
    queryClient.invalidateQueries({ queryKey: ['sync-status'] });
  };

  return (
    <div>
      <h2>Atualização</h2>
      <p>Sincroniza os dados do Jira (TEC e CAP) com o banco da dashboard.</p>

      <button onClick={handleClick} disabled={isAnyRunning}>
        {isAnyRunning ? 'Atualizando...' : 'Atualizar agora'}
      </button>

      {statuses && (
        <table className="workload-table" style={{ marginTop: '1.5rem' }}>
          <thead>
            <tr>
              <th>Site</th>
              <th>Status</th>
              <th>Última atualização</th>
              <th>Registros processados</th>
            </tr>
          </thead>
          <tbody>
            {statuses.map(({ site, last_run }) => (
              <tr key={site}>
                <td>{site}</td>
                <td>{last_run ? last_run.status : 'nunca sincronizado'}</td>
                <td>
                  {last_run?.finished_at
                    ? formatDateTime(last_run.finished_at)
                    : last_run?.status === 'running'
                      ? `em andamento desde ${formatDateTime(last_run.started_at)}`
                      : '—'}
                </td>
                <td>{last_run?.records_processed ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {statuses?.some((s) => s.last_run?.status === 'failed') && (
        <p style={{ color: '#dc2626', marginTop: '1rem' }}>
          Algum site falhou na última tentativa — veja a mensagem de erro no backend (tabela `sync_runs`).
        </p>
      )}
    </div>
  );
}
