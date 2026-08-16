import type { Team, TeamDetail, Trajectory } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Request to ${path} failed with status ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function getTeams(): Promise<Team[]> {
  return fetchJson<Team[]>("/teams");
}

export function getTeam(teamId: number): Promise<TeamDetail> {
  return fetchJson<TeamDetail>(`/teams/${teamId}`);
}

export function getTeamTrajectory(teamId: number): Promise<Trajectory> {
  return fetchJson<Trajectory>(`/teams/${teamId}/trajectory`);
}
