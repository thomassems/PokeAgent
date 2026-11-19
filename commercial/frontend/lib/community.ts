export type Profile = {
  id: number;
  email: string;
  trainer_name: string;
  city: string;
  friend_code: string;
  trainer_level: number | null;
  team: string;
  timezone: string;
  region: string;
};

export type AccountConfig = {
  official_sprites: boolean;
  share_friend_codes: boolean;
  trainer_level_min: number;
  trainer_level_max: number;
  teams: { id: string; name: string }[];
  timezones: { id: string; region: string; label: string }[];
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
