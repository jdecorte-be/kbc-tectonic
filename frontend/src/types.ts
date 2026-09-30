export interface Todo {
  id: number;
  title: string;
  description?: string | null;
  completed: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface TodoCreateInput {
  title: string;
  description?: string;
  completed?: boolean;
}

export interface TodoUpdateInput {
  title?: string;
  description?: string;
  completed?: boolean;
}

export interface HealthCheckResponse {
  status: string;
  database: string;
  timestamp: string;
}
