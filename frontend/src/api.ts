import { Todo, TodoCreateInput, TodoUpdateInput, HealthCheckResponse } from './types';

const API_BASE = '';

export async function fetchHealth(): Promise<HealthCheckResponse> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchTodos(completed?: boolean): Promise<Todo[]> {
  const url = completed !== undefined
    ? `${API_BASE}/api/todos?completed=${completed}`
    : `${API_BASE}/api/todos`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch todos: ${res.statusText}`);
  }
  return res.json();
}

export async function createTodo(input: TodoCreateInput): Promise<Todo> {
  const res = await fetch(`${API_BASE}/api/todos`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Failed to create todo: ${res.statusText}`);
  }
  return res.json();
}

export async function updateTodo(id: number, input: TodoUpdateInput): Promise<Todo> {
  const res = await fetch(`${API_BASE}/api/todos/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    throw new Error(`Failed to update todo: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteTodo(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/todos/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    throw new Error(`Failed to delete todo: ${res.statusText}`);
  }
}
