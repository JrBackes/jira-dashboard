import { apiGet } from './client';

export interface Person {
  id: number;
  display_name: string;
  email: string | null;
}

export interface HighlightItem {
  issue_key: string;
  summary: string;
  resolved_at: string | null;
}

export function fetchPeople(projectKey?: string): Promise<Person[]> {
  const qs = projectKey ? `?project=${projectKey}` : '';
  return apiGet<Person[]>(`/api/people${qs}`);
}

export function fetchPersonWorkload(personId: number, projectKey?: string): Promise<Record<string, number>> {
  const qs = projectKey ? `?project=${projectKey}` : '';
  return apiGet<Record<string, number>>(`/api/people/${personId}/workload${qs}`);
}

export function fetchPersonHighlights(personId: number, sprintId?: number): Promise<HighlightItem[]> {
  const qs = sprintId ? `?sprint_id=${sprintId}` : '';
  return apiGet<HighlightItem[]>(`/api/people/${personId}/highlights${qs}`);
}
