export interface Team {
  team_id: number;
  name: string;
  abbreviation: string;
  conference: string;
  division: string;
  logo_url: string;
  primary_color: string;
}

export interface TeamDetail extends Team {
  current_elo_rating: number | null;
  playoff_prob: number | null;
  avg_wins: number | null;
}

export interface Trajectory {
  actual: number[];
  simulated: number[][];
  final_actual_wins: number;
  games_played: number;
}
