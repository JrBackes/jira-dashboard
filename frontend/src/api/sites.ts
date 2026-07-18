import { apiGet } from './client';

export interface Site {
  id: number;
  key: string;
  name: string;
}

export function fetchSites(): Promise<Site[]> {
  return apiGet<Site[]>('/api/sites');
}
