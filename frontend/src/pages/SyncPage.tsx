import { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchSyncStatus, triggerSync } from '../api/sync';

function formatDateTime(iso: string): string {
  return new Date(`${iso}Z`).toLocaleString('pt-BR');
}

export function SyncPage() {
  const queryClient = useQueryClient();
  const [isTriggering, setIsTriggering] = useState(false);
  const [triggerError, setTriggerError] = useState<string | null>(null);

  const { data: statuses } = useQuery({
    queryKey: ['sync-status'],
    queryFn: fetchSyncStatus,
    refetchInterval: (query) => (query.state.data?.some((s) => s.last_run?.status === 'running') ? 2000 : false),
  });

  const isAnyRunning = statuses?.some((s) => s.last_run?.status === 'running') ?? false;

  // Assim que o polling confirma que nada mais está rodando, sai do estado "clicado".
  useEffect(() => {
    if (!isAnyRunning) setIsTriggering(false);
  }, [isAnyRunning]);

  const isUpdating = isTriggering || isAnyRunning;

  const handleClick = async () => {
    setTriggerError(null);
    setIsTriggering(true); // feedback imediato no clique, antes da resposta do servidor
    try {
      await triggerSync();
      await queryClient.invalidateQueries({ queryKey: ['sync-status'] });
    } catch {
      setIsTriggering(false);
      setTriggerError('Não consegui iniciar a atualização — tente de novo.');
    }
  };

  return (
    <div>
      <h2>Atualização</h2>
      <p>Sincroniza os dados do Jira (TEC e CAP) com o banco da dashboard.</p>

      <button onClick={handleClick} disabled={isUpdating}>
        {isUpdating ? 'Atualizando...' : 'Atualizar agora'}
      </button>
      {triggerError && <p style={{ color: '#dc2626' }}>{triggerError}</p>}

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
