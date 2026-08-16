import Link from "next/link";
import { notFound } from "next/navigation";
import { getTeam, getTeamTrajectory } from "@/lib/api";
import { TrajectoryChart } from "@/components/TrajectoryChart";
import styles from "./page.module.css";

export default async function TeamPage(props: PageProps<"/teams/[id]">) {
  const { id } = await props.params;
  const teamId = Number(id);

  if (!Number.isInteger(teamId)) {
    notFound();
  }

  let team;
  let trajectory;
  try {
    [team, trajectory] = await Promise.all([
      getTeam(teamId),
      getTeamTrajectory(teamId),
    ]);
  } catch {
    notFound();
  }

  return (
    <main className={styles.wrap}>
      <Link href="/" className={styles.back}>
        All teams
      </Link>

      <p className={styles.tag}>2025-26 regular season, cumulative wins</p>
      <div className={styles.fig}>
        <TrajectoryChart trajectory={trajectory} color={team.primary_color} />
      </div>
      <p className={styles.figCaption}>
        Grey shows {trajectory.simulated.length} resampled season paths
        from real pre-game Elo ratings.{" "}
        <b style={{ color: team.primary_color }}>{team.abbreviation}</b>{" "}
        shows what actually happened.
      </p>

      <h1 className={styles.teamName}>{team.name}</h1>
      <p className={styles.sub}>
        {team.conference}ern Conference, {team.division} Division
      </p>

      <div className={styles.statLine}>
        <div>
          <div className={styles.statKey}>Actual Wins</div>
          <div className={styles.statValue} style={{ color: team.primary_color }}>
            {trajectory.final_actual_wins}
          </div>
        </div>
        <div>
          <div className={styles.statKey}>Games Played</div>
          <div className={styles.statValue}>{trajectory.games_played}</div>
        </div>
        <div>
          <div className={styles.statKey}>Current Elo Rating</div>
          <div className={styles.statValue}>
            {team.current_elo_rating?.toFixed(1) ?? "N/A"}
          </div>
        </div>
        <div>
          <div className={styles.statKey}>2026-27 Playoff Odds</div>
          <div className={styles.statValue}>
            {team.playoff_prob !== null
              ? `${Math.round(team.playoff_prob * 100)}%`
              : "N/A"}
          </div>
        </div>
      </div>
    </main>
  );
}
