import type { EventDetailResponse, Task, Escalation } from '../types';
import { fetchAuthSession } from 'aws-amplify/auth';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const AUTH_MODE = import.meta.env.VITE_AUTH_MODE || 'demo';
const centralActorHeaders = { 'X-HeatOps-Role': 'central' };

const departmentActorHeaders = (department: string) => ({
  'X-HeatOps-Role': 'department',
  'X-HeatOps-Department': department,
});

async function apiFetch(input: RequestInfo | URL, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  if (AUTH_MODE === 'cognito') {
    const session = await fetchAuthSession();
    const idToken = session.tokens?.idToken;
    if (!idToken) throw new Error('Sign in is required to call the HeatOps API.');
    headers.set('Authorization', String(idToken));
    headers.delete('X-HeatOps-Role');
    headers.delete('X-HeatOps-Department');
    headers.delete('X-HeatOps-Actor');
  } else {
    for (const [name, value] of Object.entries(centralActorHeaders)) {
      if (!headers.has(name)) headers.set(name, value);
    }
  }
  return fetch(input, { ...init, headers });
}

export async function fetchHealthCheck() {
  const res = await apiFetch(`${API_BASE}/api/health`);
  return res.json();
}

export async function fetchEvents() {
  const res = await apiFetch(`${API_BASE}/api/events`);
  return res.json();
}

export async function fetchEventDetail(wardId: string): Promise<EventDetailResponse> {
  const res = await apiFetch(`${API_BASE}/api/events/${wardId}`, { headers: centralActorHeaders });
  if (!res.ok) throw new Error(`Failed to fetch event detail for ${wardId}`);
  return res.json();
}

export async function fetchTasks(): Promise<Task[]> {
  const res = await apiFetch(`${API_BASE}/api/tasks`, { headers: centralActorHeaders });
  return res.json();
}

export async function assignTaskToDepartment(taskId: string, department: string): Promise<Task> {
  const res = await apiFetch(`${API_BASE}/api/tasks/${taskId}/assign`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...centralActorHeaders },
    body: JSON.stringify({
      responsible_team: department,
      assigned_by: 'Central HeatOps Operator',
    }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new Error(data?.detail || `Failed to assign task ${taskId}`);
  }
  return res.json();
}

export async function fetchTaskStatus(taskId: string): Promise<Task> {
  const res = await apiFetch(`${API_BASE}/api/tasks/${taskId}`, { headers: centralActorHeaders });
  if (!res.ok) throw new Error(`Could not refresh status for task ${taskId}`);
  return res.json();
}

export async function fetchDepartmentTasks(department: string): Promise<Task[]> {
  const res = await apiFetch(`${API_BASE}/api/department/tasks?department=${encodeURIComponent(department)}`, {
    headers: departmentActorHeaders(department),
  });
  if (!res.ok) throw new Error(`Could not load ${department} tasks`);
  return res.json();
}

export async function updateDepartmentTaskStatus(
  taskId: string,
  department: string,
  status: string,
  failureReason?: string,
): Promise<Task> {
  const res = await apiFetch(`${API_BASE}/api/department/${encodeURIComponent(department)}/tasks/${taskId}/status`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...departmentActorHeaders(department) },
    body: JSON.stringify({
      status,
      updated_by: `${department} Operator`,
      failure_reason: failureReason || null,
    }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new Error(data?.detail || `Failed to update task ${taskId}`);
  }
  return res.json();
}

export async function retryTaskDispatch(taskId: string): Promise<Task> {
  const res = await apiFetch(`${API_BASE}/api/tasks/${taskId}/retry`, {
    method: 'POST',
    headers: centralActorHeaders,
  });
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new Error(data?.detail || `Failed to retry task ${taskId}`);
  }
  return res.json();
}

export async function triggerAgentCoordination(wardId: string) {
  const res = await apiFetch(`${API_BASE}/api/agent/coordinate/${wardId}`, {
    method: 'POST',
    headers: centralActorHeaders,
  });
  if (!res.ok) throw new Error('Agent coordination failed');
  return res.json();
}

export async function queryAgent(question: string, wardId: string = 'ward_12') {
  const res = await apiFetch(`${API_BASE}/api/agent/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...centralActorHeaders },
    body: JSON.stringify({ question, ward_id: wardId }),
  });
  if (!res.ok) throw new Error('Query agent failed');
  return res.json();
}

export async function simulateTaskOverdue(taskId: string) {
  const res = await apiFetch(`${API_BASE}/api/simulate/overdue/${taskId}`, {
    method: 'POST',
    headers: centralActorHeaders,
  });
  if (!res.ok) throw new Error('Simulation failed');
  return res.json();
}

export async function simulateWeatherChange(wardId: string, scenario: string) {
  const res = await apiFetch(`${API_BASE}/api/simulate/weather/${wardId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...centralActorHeaders },
    body: JSON.stringify({ scenario }),
  });
  if (!res.ok) throw new Error('Weather simulation failed');
  return res.json();
}

export async function fetchEscalations(): Promise<Escalation[]> {
  const res = await apiFetch(`${API_BASE}/api/escalations`, { headers: centralActorHeaders });
  return res.json();
}

export async function resetDemoData() {
  const res = await apiFetch(`${API_BASE}/api/demo/reset`, {
    method: 'POST',
    headers: centralActorHeaders,
  });
  if (!res.ok) throw new Error('Reset demo failed');
  return res.json();
}
