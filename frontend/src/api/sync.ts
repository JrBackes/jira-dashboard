import { apiGet, apiPost } from './client';

export interface SyncRunInfo {
  status: 'running' | 'success' | 'failed';
  started_at: string;
  finished_at: string | null;
  records_processed: number;
  error_message: string | null;
}

export interface SiteSyncStatus {
  site: string;
  last_run: SyncRunInfo | null;
}

export interface TriggerSyncResult {
  triggered: string[];
  already_running: string[];
}

export function fetchSyncStatus(): Promise<SiteSyncStatus[]> {
  return apiGet<SiteSyncStatus[]>('/api/sync/status');
}

export function triggerSync(): Promise<TriggerSyncResult> {
  return apiPost<TriggerSyncResult>('/api/sync/trigger');
}
