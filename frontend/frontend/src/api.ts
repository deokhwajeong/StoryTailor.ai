import { IS_DEMO } from './demo/constants';

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:5000';

async function request<T>(path: string, headers: Record<string, string>, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: body === undefined ? 'GET' : 'POST',
    headers: { 'Content-Type': 'application/json', ...headers },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error ?? 'Something went wrong.');
  return data as T;
}

// Student calls authenticate with the 8-character access code from the roster.
export async function studentApi<T>(path: string, code: string, body?: unknown): Promise<T> {
  if (IS_DEMO) {
    // Loaded only in demo builds; the normal build drops this branch.
    const { demoApi } = await import('./demo/mockApi');
    return (await demoApi(path, code, body)) as T;
  }
  return request<T>(path, { 'X-Student-Code': code }, body);
}

// Teacher calls authenticate with the bearer token printed by `flask create-teacher`.
export async function teacherApi<T>(path: string, token: string): Promise<T> {
  if (IS_DEMO) {
    const { demoTeacherApi } = await import('./demo/mockApi');
    return (await demoTeacherApi(path, token)) as T;
  }
  return request<T>(path, { Authorization: `Bearer ${token}` });
}
