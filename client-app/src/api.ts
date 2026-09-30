import { User, HealthCheckResponse } from './types';

const API_BASE = '';

export async function fetchHealth(): Promise<HealthCheckResponse> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchUsers(): Promise<User[]> {
  const res = await fetch(`${API_BASE}/api/users`);
  if (!res.ok) {
    throw new Error(`Failed to fetch users: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchUserDetail(id: number): Promise<User> {
  const res = await fetch(`${API_BASE}/api/users/${id}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch user details for ID ${id}`);
  }
  return res.json();
}

export async function triggerSeed(): Promise<void> {
  const res = await fetch(`${API_BASE}/api/seed?force=true`, {
    method: 'POST',
  });
  if (!res.ok) {
    throw new Error(`Failed to seed database`);
  }
}
