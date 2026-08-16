from sqlalchemy import select

from ingestion.db import Session
from ingestion.models import Game
from ratings.evaluate import evaluate_season

K_FACTOR_CANDIDATES = [4, 6, 8, 10, 12, 15, 20]
MOV_SCALE_CANDIDATES = [1.0, 2.2, 4.0, 8.0]


def load_games() -> list[dict]:
    with Session() as session:
        rows = session.scalars(
            select(Game)
            .where(Game.is_playoff.is_(False), Game.home_score.is_not(None))
            .order_by(Game.date, Game.game_id)
        ).all()
        return [
            {
                "home_team_id": g.home_team_id,
                "away_team_id": g.away_team_id,
                "home_score": g.home_score,
                "away_score": g.away_score,
                "date": g.date,
                "credited_margin": g.credited_margin,
            }
            for g in rows
        ]


def main() -> None:
    games = load_games()
    print(f"Evaluating against {len(games)} regular-season games\n")

    results = []
    for k in K_FACTOR_CANDIDATES:
        for mov_scale in MOV_SCALE_CANDIDATES:
            result = evaluate_season(games, k_factor=k, mov_scale=mov_scale)
            results.append(result)
            print(
                f"k={k:>5.1f}  mov_scale={mov_scale:>4.1f}  "
                f"brier={result['brier_score']:.4f}  "
                f"log_loss={result['log_loss']:.4f}  "
                f"spread={result['rating_spread']:.0f}"
            )

    best = min(results, key=lambda r: r["log_loss"])
    print(
        f"\nBest by log loss: k={best['k_factor']}, mov_scale={best['mov_scale']}, "
        f"log_loss={best['log_loss']:.4f}, spread={best['rating_spread']:.0f}"
    )


if __name__ == "__main__":
    main()
