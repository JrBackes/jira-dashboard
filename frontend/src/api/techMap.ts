import { apiGet, apiPost } from './client';

export interface TechMapInfo {
  tarefa: string;
  status: string | null;
  frente: string | null;
  ice_score: number | null;
  entrega: string | null;
}

export interface TechMapGroup {
  epic_key: string | null;
  epic_summary: string | null;
  issue_count: number;
  tech_map: TechMapInfo | null;
}

export function fetchTechMapForSprint(sprintId: number): Promise<TechMapGroup[]> {
  return apiGet<TechMapGroup[]>(`/api/tech-map/sprints/${sprintId}`);
}

export function importTechMap(tsv: string): Promise<{ entries_imported: number }> {
  return apiPost<{ entries_imported: number }>('/api/tech-map/import', { tsv });
}
