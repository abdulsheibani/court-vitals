import Link from "next/link";
import { getTeams } from "@/lib/api";
import styles from "./page.module.css";

export default async function HomePage() {
  const teams = await getTeams();
  const byConference = {
    East: teams.filter((t) => t.conference === "East"),
    West: teams.filter((t) => t.conference === "West"),
  };

  return (
    <main className={styles.wrap}>
      <header className={styles.intro}>
        <p className={styles.eyebrow}>Court Vitals</p>
        <h1 className={styles.h1}>Every team&apos;s season, real and simulated</h1>
        <p className={styles.lede}>
          Not affiliated with the NBA. No relation to gambling or betting in
          any form. Figures below come from a from-scratch Elo rating engine
          and season simulation, shown to demonstrate statistical modeling.
        </p>
      </header>

      {(["East", "West"] as const).map((conference) => (
        <section key={conference} className={styles.conference}>
          <h2 className={styles.conferenceName}>{conference}ern Conference</h2>
          <ul className={styles.teamList}>
            {byConference[conference].map((team) => (
              <li key={team.team_id}>
                <Link href={`/teams/${team.team_id}`} className={styles.teamLink}>
                  <span
                    className={styles.dot}
                    style={{ background: team.primary_color }}
                  />
                  <span className={styles.teamName}>{team.name}</span>
                  <span className={styles.division}>{team.division}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </main>
  );
}
