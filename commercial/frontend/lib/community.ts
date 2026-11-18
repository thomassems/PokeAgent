export type Profile = {
  id: number;
  email: string;
  trainer_name: string;
  city: string;
  friend_code: string;
};

export async function communityFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    credentials: "same-origin",
    headers: {
      "content-type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (response.status === 204) return undefined as T;
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      body && typeof body === "object" && "detail" in body && typeof body.detail === "string"
        ? body.detail
        : "Request failed.";
    throw new Error(detail);
  }
  return body as T;
}
