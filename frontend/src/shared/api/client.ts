const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export function getApiUrl(): string {
  return API_URL
}

export async function apiClient(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const url = path.startsWith('http') ? path : `${API_URL}${path}`
  return fetch(url, init)
}