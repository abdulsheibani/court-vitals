"use client";

import { scaleLinear } from "@visx/scale";
import { useEffect, useRef } from "react";
import type { Trajectory } from "@/lib/types";

interface TrajectoryChartProps {
  trajectory: Trajectory;
  color: string;
  animationMs?: number;
}

export function TrajectoryChart({
  trajectory,
  color,
  animationMs = 1600,
}: TrajectoryChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;

    const allSeries = [...trajectory.simulated, trajectory.actual];
    const maxWins = Math.max(1, ...allSeries.flat());
    const maxGames = trajectory.actual.length - 1;

    // Canvas's strokeStyle can't read CSS custom properties directly (that
    // only works for actual DOM rendering), so resolve the token to a real
    // color value up front.
    const simulatedColor = getComputedStyle(canvas).getPropertyValue("--color-simulated").trim() || "#C7CDD6";

    let rafId = 0;

    function draw(revealGames: number) {
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas!.getBoundingClientRect();
      canvas!.width = rect.width * dpr;
      canvas!.height = rect.height * dpr;
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx!.clearRect(0, 0, rect.width, rect.height);

      const xScale = scaleLinear({
        domain: [0, maxGames],
        range: [4, rect.width - 4],
      });
      const yScale = scaleLinear({
        domain: [0, maxWins],
        range: [rect.height - 10, 10],
      });

      const drawSeries = (series: number[], strokeStyle: string, lineWidth: number, alpha: number) => {
        ctx!.strokeStyle = strokeStyle;
        ctx!.lineWidth = lineWidth;
        ctx!.globalAlpha = alpha;
        ctx!.lineJoin = "round";
        ctx!.beginPath();

        const wholePoints = Math.floor(revealGames);
        for (let i = 0; i <= wholePoints && i < series.length; i++) {
          const x = xScale(i);
          const y = yScale(series[i]);
          if (i === 0) ctx!.moveTo(x, y);
          else ctx!.lineTo(x, y);
        }

        // Partial segment into the next point, for a smooth (not stepped) reveal.
        const frac = revealGames - wholePoints;
        if (frac > 0 && wholePoints + 1 < series.length) {
          const w0 = series[wholePoints];
          const w1 = series[wholePoints + 1];
          const interpWins = w0 + (w1 - w0) * frac;
          ctx!.lineTo(xScale(wholePoints + frac), yScale(interpWins));
        }

        ctx!.stroke();
      };

      trajectory.simulated.forEach((series) => drawSeries(series, simulatedColor, 1, 0.55));
      drawSeries(trajectory.actual, color, 2.5, 1);

      const revealedIdx = Math.min(revealGames, maxGames);
      const wholeIdx = Math.floor(revealedIdx);
      const frac = revealedIdx - wholeIdx;
      const w0 = trajectory.actual[wholeIdx];
      const w1 = trajectory.actual[Math.min(wholeIdx + 1, maxGames)];
      const dotWins = w0 + (w1 - w0) * frac;
      ctx!.globalAlpha = 1;
      ctx!.fillStyle = color;
      ctx!.beginPath();
      ctx!.arc(xScale(revealedIdx), yScale(dotWins), 4, 0, Math.PI * 2);
      ctx!.fill();
    }

    if (prefersReducedMotion) {
      draw(maxGames);
      return;
    }

    const startTime = performance.now();
    function tick(now: number) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / animationMs, 1);
      draw(progress * maxGames);
      if (progress < 1) {
        rafId = requestAnimationFrame(tick);
      }
    }
    rafId = requestAnimationFrame(tick);

    function handleResize() {
      draw(maxGames);
    }
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener("resize", handleResize);
    };
  }, [trajectory, color, animationMs]);

  return (
    <canvas
      ref={canvasRef}
      role="img"
      aria-label={`Cumulative wins over the season: ${trajectory.final_actual_wins} actual wins across ${trajectory.games_played} games, plotted against ${trajectory.simulated.length} simulated season paths.`}
      style={{ width: "100%", height: "100%", display: "block" }}
    />
  );
}
