import { useQuery } from '@tanstack/react-query';
import { BurndownChart } from '../components/charts/BurndownChart';
import { VelocityChart } from '../components/charts/VelocityChart';
import {
  fetchSprintBurndown,
  fetchSprintScopeChanges,
  fetchSprintSummary,
  fetchSprintVelocityHistory,
  fetchSprints,
} from '../api/sprints';
import { useSelectedProject } from '../hooks/useSelectedProject';
import { statusCategoryLabel } from '../lib/statusCategory';

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
              <li key={status}>{statusCategoryLabel(status)}: {count}</li>
            ))}
          </ul>
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
