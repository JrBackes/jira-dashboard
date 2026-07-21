import { useQuery } from '@tanstack/react-query';
import { BlockedItemsPanel } from '../components/BlockedItemsPanel';
import { BurndownChart } from '../components/charts/BurndownChart';
import { VelocityChart } from '../components/charts/VelocityChart';
import { SprintRiskPanel } from '../components/SprintRiskPanel';
import { SprintWorkloadTable } from '../components/SprintWorkloadTable';
import { TechMapPanel } from '../components/TechMapPanel';
import {
  fetchSprintBlocked,
  fetchSprintBurndown,
  fetchSprintRisk,
  fetchSprintScopeChanges,
  fetchSprintSummary,
  fetchSprintVelocityHistory,
  fetchSprintWorkloadByStatus,
  fetchSprints,
} from '../api/sprints';
import { fetchTechMapForSprint } from '../api/techMap';
import { useSelectedProject } from '../hooks/useSelectedProject';

export function CurrentSprintPage() {
  const { projectKey } = useSelectedProject();

  const { data: activeSprints } = useQuery({
    queryKey: ['sprints', projectKey, 'active'],
    queryFn: () => fetchSprints(projectKey, 'active'),
  });
  const sprint = activeSprints?.[0];
  const sprintId = sprint?.id;

  const { data: summary } = useQuery({
    queryKey: ['sprint-summary', sprintId],
    queryFn: () => fetchSprintSummary(sprintId!),
    enabled: !!sprintId,
  });
  const { data: scopeChanges } = useQuery({
    queryKey: ['sprint-scope-changes', sprintId],
    queryFn: () => fetchSprintScopeChanges(sprintId!),
    enabled: !!sprintId,
  });
  const { data: burndown } = useQuery({
    queryKey: ['sprint-burndown', sprintId],
    queryFn: () => fetchSprintBurndown(sprintId!),
    enabled: !!sprintId,
  });
  const { data: velocity } = useQuery({
    queryKey: ['sprint-velocity', sprintId],
    queryFn: () => fetchSprintVelocityHistory(sprintId!),
    enabled: !!sprintId,
  });
  const { data: workloadByStatus } = useQuery({
    queryKey: ['sprint-workload-by-status', sprintId],
    queryFn: () => fetchSprintWorkloadByStatus(sprintId!),
    enabled: !!sprintId,
  });
  const { data: risk } = useQuery({
    queryKey: ['sprint-risk', sprintId],
    queryFn: () => fetchSprintRisk(sprintId!),
    enabled: !!sprintId,
  });
  const { data: blocked } = useQuery({
    queryKey: ['sprint-blocked', sprintId],
    queryFn: () => fetchSprintBlocked(sprintId!),
    enabled: !!sprintId,
  });
  const { data: techMap } = useQuery({
    queryKey: ['sprint-tech-map', sprintId],
    queryFn: () => fetchTechMapForSprint(sprintId!),
    enabled: !!sprintId,
  });

  if (!activeSprints) return <p>Carregando...</p>;
  if (!sprint) return <p>Nenhuma sprint ativa encontrada para {projectKey}. Rode o sync do Jira primeiro.</p>;

  return (
    <div>
      <h2>Sprint Atual — {sprint.name}</h2>
      {sprint.goal && <p><em>{sprint.goal}</em></p>}

      {summary && (
        <section>
          <h3>Contagem por status</h3>
          <ul>
            {Object.entries(summary.status_counts).map(([status, count]) => (
              <li key={status}>{status}: {count}</li>
            ))}
          </ul>
        </section>
      )}

      {risk && (
        <section>
          <h3>Itens em risco</h3>
          <SprintRiskPanel data={risk} />
        </section>
      )}

      {blocked && (
        <section>
          <h3>Itens bloqueados</h3>
          <BlockedItemsPanel items={blocked} />
        </section>
      )}

      {techMap && (
        <section>
          <h3>Mapa de Tecnologia</h3>
          <TechMapPanel groups={techMap} />
        </section>
      )}

      {workloadByStatus && (
        <section>
          <h3>Carga de trabalho por status e colaborador</h3>
          <p style={{ fontSize: '0.85rem', color: '#64748b' }}>
            Tempo = estimativa original antes de chegar em "To Test"; tempo gasto (apontado manualmente) depois disso.
          </p>
          <SprintWorkloadTable data={workloadByStatus} />
        </section>
      )}

      {burndown && burndown.length > 0 && (
        <section>
          <h3>Burndown</h3>
          <BurndownChart data={burndown} />
        </section>
      )}

      {velocity && velocity.length > 0 && (
        <section>
          <h3>Histórico de Velocity</h3>
          <VelocityChart data={velocity} />
        </section>
      )}

      {scopeChanges && (
        <section>
          <h3>Mudanças de escopo durante a sprint</h3>
          <p>Entraram: {scopeChanges.added.length} · Saíram: {scopeChanges.removed.length}</p>
          <ul>
            {scopeChanges.added.map((item) => (
              <li key={item.issue_key}>+ {item.issue_key} — {item.summary}</li>
            ))}
            {scopeChanges.removed.map((item) => (
              <li key={item.issue_key}>− {item.issue_key} — {item.summary}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
