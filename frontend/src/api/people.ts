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

export function fetchPersonWorkload(
  personId: number,
  projectKey?: string,
  sprintId?: number,
): Promise<Record<string, number>> {
  const params = new URLSearchParams();
  if (projectKey) params.set('project', projectKey);
  if (sprintId) params.set('sprint_id', String(sprintId));
  const qs = params.toString();
  return apiGet<Record<string, number>>(`/api/people/${personId}/workload${qs ? `?${qs}` : ''}`);
}

export function fetchPersonHighlights(personId: number, sprintId?: number): Promise<HighlightItem[]> {
  const qs = sprintId ? `?sprint_id=${sprintId}` : '';
  return apiGet<HighlightItem[]>(`/api/people/${personId}/highlights${qs}`);
}

export interface WeeklyRankingRow {
  person: string;
  seconds: number;
  percent_of_expected: number;
}

export interface WeeklyTimeRanking {
  week_start: string;
  week_end: string;
  expected_seconds: number;
  ranking: WeeklyRankingRow[];
}

export function fetchWeeklyTimeRanking(projectKey?: string, sprintId?: number): Promise<WeeklyTimeRanking> {
  const params = new URLSearchParams();
  if (projectKey) params.set('project', projectKey);
  if (sprintId) params.set('sprint_id', String(sprintId));
  const qs = params.toString();
  return apiGet<WeeklyTimeRanking>(`/api/people/ranking/weekly${qs ? `?${qs}` : ''}`);
}

export interface DailyRankingRow {
  person: string;
  cells: Record<string, number>;
  total_seconds: number;
  expected_total_seconds: number;
}

export interface DailyTimeBreakdown {
  days: string[];
  expected_per_day_seconds: number;
  rows: DailyRankingRow[];
}

export function fetchDailyTimeBreakdown(projectKey?: string, sprintId?: number): Promise<DailyTimeBreakdown> {
  const params = new URLSearchParams();
  if (projectKey) params.set('project', projectKey);
  if (sprintId) params.set('sprint_id', String(sprintId));
  const qs = params.toString();
  return apiGet<DailyTimeBreakdown>(`/api/people/ranking/daily${qs ? `?${qs}` : ''}`);
}
