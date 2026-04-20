from __future__ import annotations

import argparse

from app.database import SessionLocal
from app.services.simulation_service import export_simulation_payload, run_simulation


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Aureonics simulation and export JSON output.")
    parser.add_argument("--steps", type=int, default=150)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--k", type=float, default=4.0)
    parser.add_argument("--dt", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--output", type=str, default="simulation_latest.json")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        profiles = run_simulation(
            db,
            steps=args.steps,
            alpha=args.alpha,
            k=args.k,
            dt=args.dt,
            seed=args.seed,
        )
    finally:
        db.close()

    payload = {
        "steps": args.steps,
        "alpha": args.alpha,
        "k": args.k,
        "dt": args.dt,
        "seed": args.seed,
        "profiles": profiles,
    }
    path = export_simulation_payload(payload, args.output)
    print(f"Simulation exported to {path}")


if __name__ == "__main__":
    main()
