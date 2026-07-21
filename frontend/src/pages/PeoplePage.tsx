import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  fetchDailyTimeBreakdown,
  fetchPeople,
  fetchPersonHighlights,
  fetchPersonWorkload,
  fetchWeeklyTimeRanking,
} from '../api/people';
import { fetchSprints } from '../api/sprints';
import { WorkloadBarChart } from '../components/charts/WorkloadBarChart';
import { DailyRankingTable } from '../components/DailyRankingTable';
import { WeeklyRankingTable } from '../components/WeeklyRankingTable';
import { useSelectedProject } from '../hooks/useSelectedProject';

const ALL_SPRINTS = 'all' as const;

export function PeoplePage() {
  const { projectKey } = useSelectedProject();
  const [selectedPersonId, setSelectedPersonId] = useState<number | null>(null);
  const [selectedSprintId, setSelectedSprintId] = useState<number | typeof ALL_SPRINTS | null>(null);

  const { data: people } = useQuery({
    queryKey: ['people', projectKey],
    queryFn: () => fetchPeople(projectKey),
  });
  const { data: sprints } = useQuery({
    queryKey: ['sprints', projectKey, 'all-for-people-page'],
    queryFn: () => fetchSprints(projectKey),
  });

  const personId = selectedPersonId ?? people?.[0]?.id ?? null;

  // Padrão: sprint atualmente ativa, se houver — usuário pode trocar pra uma sprint
  // específica ou "todas" via seletor.
  const activeSprintId = sprints?.find((sprint) => sprint.state === 'active')?.id;
  const sprintFilter = selectedSprintId ?? activeSprintId ?? ALL_SPRINTS;
  const sprintIdParam = sprintFilter === ALL_SPRINTS ? undefined : sprintFilter;

  const { data: workload } = useQuery({
    queryKey: ['person-workload', personId, projectKey, sprintIdParam],
    queryFn: () => fetchPersonWorkload(personId!, projectKey, sprintIdParam),
    enabled: !!personId,
  });
  const { data: highlights } = useQuery({
    queryKey: ['person-highlights', personId, sprintIdParam],
    queryFn: () => fetchPersonHighlights(personId!, sprintIdParam),
    enabled: !!personId,
  });
  const { data: weeklyRanking } = useQuery({
    queryKey: ['weekly-time-ranking', projectKey, sprintIdParam],
    queryFn: () => fetchWeeklyTimeRanking(projectKey, sprintIdParam),
  });
  const { data: dailyBreakdown } = useQuery({
    queryKey: ['daily-time-breakdown', projectKey, sprintIdParam],
    queryFn: () => fetchDailyTimeBreakdown(projectKey, sprintIdParam),
  });

  if (!people) return <p>Carregando...</p>;
  if (people.length === 0) return <p>Nenhuma pessoa sincronizada para {projectKey} ainda.</p>;

  return (
    <div>
      <h2>Por Pessoa</h2>

      <label htmlFor="sprint-select">Sprint:</label>{' '}
      <select
        id="sprint-select"
        value={sprintFilter}
        onChange={(e) => setSelectedSprintId(e.target.value === ALL_SPRINTS ? ALL_SPRINTS : Number(e.target.value))}
      >
        <option value={ALL_SPRINTS}>Todas as sprints</option>
        {sprints?.map((sprint) => (
          <option key={sprint.id} value={sprint.id}>
            {sprint.name}{sprint.state === 'active' ? ' (atual)' : ''}
          </option>
        ))}
      </select>

      {weeklyRanking && (
        <section>
          <h3>Ranking da semana — tempo trabalhado</h3>
          <WeeklyRankingTable data={weeklyRanking} />
        </section>
      )}

      {dailyBreakdown && (
        <section>
          <h3>Ranking diário — ritmo de entrega</h3>
          <DailyRankingTable data={dailyBreakdown} />
        </section>
      )}

      <label htmlFor="person-select">Pessoa:</label>{' '}
      <select
        id="person-select"
        value={personId ?? ''}
        onChange={(e) => setSelectedPersonId(Number(e.target.value))}
      >
        {people.map((person) => (
          <option key={person.id} value={person.id}>{person.display_name}</option>
        ))}
      </select>

      {workload && (
        <section>
          <h3>Carga de trabalho atual</h3>
          <WorkloadBarChart data={workload} />
        </section>
      )}

      {highlights && (
        <section>
          <h3>Entregas em destaque</h3>
          <ul>
            {highlights.map((item) => (
              <li key={item.issue_key}>{item.issue_key} — {item.summary}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
