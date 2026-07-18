import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchPeople, fetchPersonHighlights, fetchPersonWorkload } from '../api/people';
import { WorkloadBarChart } from '../components/charts/WorkloadBarChart';
import { useSelectedProject } from '../hooks/useSelectedProject';

export function PeoplePage() {
  const { projectKey } = useSelectedProject();
  const [selectedPersonId, setSelectedPersonId] = useState<number | null>(null);

  const { data: people } = useQuery({
    queryKey: ['people', projectKey],
    queryFn: () => fetchPeople(projectKey),
  });

  const personId = selectedPersonId ?? people?.[0]?.id ?? null;

  const { data: workload } = useQuery({
    queryKey: ['person-workload', personId, projectKey],
    queryFn: () => fetchPersonWorkload(personId!, projectKey),
    enabled: !!personId,
  });
  const { data: highlights } = useQuery({
    queryKey: ['person-highlights', personId],
    queryFn: () => fetchPersonHighlights(personId!),
    enabled: !!personId,
  });

  if (!people) return <p>Carregando...</p>;
  if (people.length === 0) return <p>Nenhuma pessoa sincronizada para {projectKey} ainda.</p>;

  return (
    <div>
      <h2>Por Pessoa</h2>

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
