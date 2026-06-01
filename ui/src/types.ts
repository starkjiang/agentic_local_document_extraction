export type JobStatus = 'pending' | 'extracting' | 'validating' | 'synthesizing' | 'completed' | 'failed' | 'retrying';
export type DocumentType = 'invoice' | 'contract' | 'report' | 'academic' | 'form' | 'unknown';

export interface JobState {
  job_id: string;
  status: JobStatus;
  filename: string;
  created_at: number;
  current_step: string;
  logs: Array<{ timestamp: string; step: string; message: string; level: string }>;
  errors: string[];
  warnings: string[];
  result?: any;
  markdown?: string;
  extraction_result?: any;
  validation_result?: any;
}

export interface HealthStatus {
  status: string;
  ollama_available: boolean;
  ollama_models: string[];
  vector_store_stats: { total_documents: number; collection_name: string };
  version: string;
}
