import { apiGet } from './client';

export interface Sprint {
  id: number;
  name: string;
  state: 'future' | 'active' | 'closed';
  start_date: string | null;
  end_date: string | null;
  goal: string | null;
}

export interface SprintSummary {
  sprint: Sprint;
  status_counts: Record<string, number>;
}

export interface ScopeChangeItem {
  issue_key: string;
  summary: string;
  changed_at: string;
}

export interface SprintScopeChanges {
  added: ScopeChangeItem[];
  removed: ScopeChangeItem[];
}

export interface BurndownPoint {
  day: string;
  remaining_issues: number;
  remaining_points: number;
}

export interface VelocityPoint {
  sprint_id: number;
  sprint_name: string;
  planned_points: number;
  delivered_points: number;
}

export interface WorkloadCell {
  count: number;
  seconds: number;
}

export interface WorkloadByStatus {
  statuses: string[];
  rows: { person: string; cells: Record<string, WorkloadCell> }[];
}

export function fetchSprints(projectKey?: string, state?: string): Promise<Sprint[]> {
  const params = new URLSearchParams();
  if (projectKey) params.set('project', projectKey);
  if (state) params.set('state', state);
  const qs = params.toString();
  return apiGet<Sprint[]>(`/api/sprints${qs ? `?${qs}` : ''}`);
}

export function fetchSprintSummary(sprintId: number): Promise<SprintSummary> {
  return apiGet<SprintSummary>(`/api/sprints/${sprintId}/summary`);
}

export function fetchSprintScopeChanges(sprintId: number): Promise<SprintScopeChanges> {
  return apiGet<SprintScopeChanges>(`/api/sprints/${sprintId}/scope-changes`);
}

export function fetchSprintBurndown(sprintId: number): Promise<BurndownPoint[]> {
  return apiGet<BurndownPoint[]>(`/api/sprints/${sprintId}/burndown`);
}

export function fetchSprintVelocityHistory(sprintId: number): Promise<VelocityPoint[]> {
  return apiGet<VelocityPoint[]>(`/api/sprints/${sprintId}/velocity-history`);
}

export function fetchSprintWorkloadByStatus(sprintId: number): Promise<WorkloadByStatus> {
  return apiGet<WorkloadByStatus>(`/api/sprints/${sprintId}/workload-by-status`);
}
