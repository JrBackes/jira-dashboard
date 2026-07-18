import { useEffect, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchSyncStatus, triggerSync } from '../api/sync';

function formatDateTime(iso: string): string {
  return new Date(`${iso}Z`).toLocaleString('pt-BR');
}

// Tempo máximo que o botão fica em "Atualizando..." antes de destravar sozinho, mesmo que
// o polling nunca confirme o fim do sync (ex: falha silenciosa antes de criar o SyncRun).
const SAFETY_TIMEOUT_MS = 3 * 60 * 1000;

export function SyncPage() {
  const queryClient = useQueryClient();
  const [isTriggering, setIsTriggering] = useState(false);
  const [hasSeenRunning, setHasSeenRunning] = useState(false);
  const [triggerError, setTriggerError] = useState<string | null>(null);
  const wasUpdatingRef = useRef(false);

  // refetchInterval como valor reativo simples (não como função inspecionando query.state.data) —
  // continua fazendo polling enquanto estamos "no meio" de uma atualização disparada por nós,
  // e também quando detectamos (ou já detectamos) uma sprint rodando de outra origem (CLI, outra aba).
  const { data: statuses } = useQuery({
    queryKey: ['sync-status'],
    queryFn: fetchSyncStatus,
    refetchInterval: isTriggering || hasSeenRunning ? 2000 : false,
  });

  const isAnyRunning = statuses?.some((s) => s.last_run?.status === 'running') ?? false;
  const isUpdating = isTriggering || isAnyRunning;

  useEffect(() => {
    if (isAnyRunning) setHasSeenRunning(true);
  }, [isAnyRunning]);

  // Só destrava quando já vimos "running" pelo menos uma vez E agora já não está mais —
  // evita destravar cedo demais por causa de uma resposta ainda desatualizada logo após o clique.
  useEffect(() => {
    if (hasSeenRunning && !isAnyRunning) {
      setIsTriggering(false);
      setHasSeenRunning(false);
    }
  }, [hasSeenRunning, isAnyRunning]);

  // Salvaguarda: nunca fica preso em "Atualizando..." para sempre.
  useEffect(() => {
    if (!isTriggering) return;
    const timeout = setTimeout(() => {
      setIsTriggering(false);
      setHasSeenRunning(false);
    }, SAFETY_TIMEOUT_MS);
    return () => clearTimeout(timeout);
  }, [isTriggering]);

  // Quando uma atualização termina, os dados de sprint/pessoas ficaram desatualizados no cache
  // de outras páginas — invalida tudo pra não precisar recarregar a página manualmente.
  useEffect(() => {
    if (wasUpdatingRef.current && !isUpdating) {
      queryClient.invalidateQueries();
    }
    wasUpdatingRef.current = isUpdating;
  }, [isUpdating, queryClient]);

  const handleClick = async () => {
    setTriggerError(null);
    setHasSeenRunning(false);
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
