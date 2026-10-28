"""Synthetic network engine for Ghost Network India.

All topology metrics and failures are simulated. Timings measured with perf_counter
represent local Python algorithm execution, not real telecom recovery latency.
"""
from __future__ import annotations

import random
import time
from typing import Any

import networkx as nx


def forecast_link_risk(history: dict[str, list[float]], threshold: float = 65.0) -> dict[str, Any]:
    """Transparent trend heuristic using only observations before the forecast point."""
    weights = {"congestion_pct": 0.45, "packet_loss_pct": 0.30, "latency_ms": 0.25}
    normalized = {}
    slopes = {}
    for key, values in history.items():
        vals = [float(v) for v in values]
        if len(vals) < 2:
            slopes[key] = 0.0
            normalized[key] = vals[-1] if vals else 0.0
        else:
            slopes[key] = (vals[-1] - vals[0]) / (len(vals) - 1)
            normalized[key] = vals[-1]
    congestion = min(100.0, max(0.0, normalized.get("congestion_pct", 0.0)))
    loss = min(100.0, max(0.0, normalized.get("packet_loss_pct", 0.0) * 10))
    latency = min(100.0, max(0.0, normalized.get("latency_ms", 0.0) * 2))
    trend_pressure = (
        min(100.0, max(0.0, slopes.get("congestion_pct", 0.0) * 2.0)) * 0.45
        + min(100.0, max(0.0, slopes.get("packet_loss_pct", 0.0) * 20.0)) * 0.30
        + min(100.0, max(0.0, slopes.get("latency_ms", 0.0) * 4.0)) * 0.25
    )
    current_pressure = congestion * 0.45 + loss * 0.30 + latency * 0.25
    score = round(min(100.0, max(0.0, current_pressure * 0.65 + trend_pressure * 0.35)), 1)
    increasing = any(v > 0 for v in slopes.values())
    return {
        "risk_score": score,
        "warning": bool(score >= threshold and increasing),
        "trend": "DEGRADING" if increasing else "STABLE",
        "slopes": {k: round(v, 4) for k, v in slopes.items()},
        "threshold": threshold,
        "observations": min((len(v) for v in history.values()), default=0),
    }


def _safe_route(graph: nx.Graph, source: Any, destination: Any) -> list:
    if source not in graph or destination not in graph:
        return []
    try:
        return nx.shortest_path(graph, source, destination, weight="composite_cost")
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []


def measured_recovery(graph: nx.Graph, source: Any, destination: Any, primary_route: list) -> dict[str, Any]:
    """Measure actual Python computation for route/backup operations."""
    failed_edge = tuple(primary_route[:2]) if len(primary_route) >= 2 else None
    backup_graph = graph.copy()
    precompute_start = time.perf_counter()
    backup_route = []
    if failed_edge and backup_graph.has_edge(*failed_edge):
        backup_graph.remove_edge(*failed_edge)
        backup_route = _safe_route(backup_graph, source, destination)
    precompute_ms = (time.perf_counter() - precompute_start) * 1000

    reactive_graph = graph.copy()
    if failed_edge and reactive_graph.has_edge(*failed_edge):
        reactive_graph.remove_edge(*failed_edge)
    reactive_start = time.perf_counter()
    reactive_route = _safe_route(reactive_graph, source, destination)
    reactive_ms = (time.perf_counter() - reactive_start) * 1000

    switch_start = time.perf_counter()
    switched_route = backup_route[:] if backup_route else []
    switch_ms = (time.perf_counter() - switch_start) * 1000
    return {
        "failed_edge": failed_edge,
        "reactive_route": reactive_route,
        "backup_route": backup_route,
        "switched_route": switched_route,
        "precompute_ms": precompute_ms,
        "reactive_ms": reactive_ms,
        "proactive_ms": switch_ms,
        "recovery_success": bool(switched_route),
        "route_cost": _route_cost(backup_graph, switched_route),
    }


def _route_cost(graph: nx.Graph, route: list) -> float | None:
    if not route or any(not graph.has_edge(a, b) for a, b in zip(route, route[1:])):
        return None
    return round(sum(float(graph[a][b].get("composite_cost", graph[a][b].get("weight", 1))) for a, b in zip(route, route[1:])), 3)


def _valid_route(graph: nx.Graph, route: list, source: Any, destination: Any) -> bool:
    return bool(route and route[0] == source and route[-1] == destination
                and all(graph.has_edge(a, b) for a, b in zip(route, route[1:])))


def run_seeded_stress_tests(graph: nx.Graph, source: Any, destination: Any,
                            runs: int = 30, seed: int = 42, max_failures: int = 3) -> dict[str, Any]:
    """Repeat seeded synthetic edge-failure and congestion scenarios."""
    rng = random.Random(seed)
    successes, disconnected, costs, times_ms = 0, 0, [], []
    scenario_rows = []
    base_edges = list(graph.edges())
    if not base_edges:
        return {"seed": seed, "runs": runs, "success_rate_pct": 0.0,
                "disconnected_scenarios": runs, "mean_route_cost": None,
                "mean_recovery_ms": None, "message": "Graph contains no links.",
                "scenario_rows": []}
    for i in range(max(1, int(runs))):
        g = graph.copy()
        count = min(len(base_edges), rng.randint(1, max(1, max_failures)))
        failed = rng.sample(base_edges, count)
        for u, v in failed:
            if g.has_edge(u, v):
                g.remove_edge(u, v)
        # Apply seeded congestion changes to remaining links.
        for u, v, data in g.edges(data=True):
            data["congestion_pct"] = min(100, max(0, float(data.get("congestion_pct", 50)) + rng.randint(-15, 25)))
            data["composite_cost"] = round(
                float(data.get("composite_cost", 1)) + max(0, data["congestion_pct"] - 50) * 0.08, 3
            )
        start = time.perf_counter()
        route = _safe_route(g, source, destination)
        elapsed = (time.perf_counter() - start) * 1000
        ok = _valid_route(g, route, source, destination)
        if ok:
            successes += 1
            costs.append(_route_cost(g, route))
        else:
            disconnected += 1
        times_ms.append(elapsed)
        scenario_rows.append({
            "scenario": i + 1, "failed_links": len(failed), "recovered": ok,
            "route_cost": _route_cost(g, route), "recovery_ms": round(elapsed, 5),
        })
    total = max(1, int(runs))
    return {
        "seed": seed, "runs": total,
        "success_rate_pct": round(successes / total * 100, 2),
        "disconnected_scenarios": disconnected,
        "mean_route_cost": round(sum(costs) / len(costs), 3) if costs else None,
        "mean_recovery_ms": round(sum(times_ms) / len(times_ms), 5) if times_ms else None,
        "message": "Synthetic seeded stress test; measured values are local simulator results.",
        "scenario_rows": scenario_rows,
    }


def evaluate_forecast_early_warning(samples: int = 100, seed: int = 42) -> dict[str, Any]:
    """Evaluate a trend score against a separately generated next-step failure label.

    Synthetic data only. Four observations are scored; the fifth observation is used
    to label failure, so the target is not included in the predictor history.
    """
    rng = random.Random(seed)
    tp = fp = tn = fn = 0
    for _ in range(max(1, int(samples))):
        level = rng.uniform(15, 70)
        slope = rng.uniform(-3, 15)
        noise = [rng.uniform(-2, 2) for _ in range(5)]
        congestion = [min(100, max(0, level + slope * i + noise[i])) for i in range(5)]
        loss_base = rng.uniform(0.05, 1.5)
        loss = [min(10, max(0.01, loss_base + max(0, slope) * i * 0.025 + rng.uniform(-0.1, 0.1))) for i in range(5)]
        latency_base = rng.uniform(5, 80)
        latency = [max(1, latency_base + max(0, slope) * i * 0.35 + rng.uniform(-2, 2)) for i in range(5)]
        # The target is determined only from the held-out fifth observation.
        actual_failure = congestion[4] >= 88 or (loss[4] >= 3.5 and latency[4] >= 75)
        history = {"congestion_pct": congestion[:4], "packet_loss_pct": loss[:4], "latency_ms": latency[:4]}
        predicted = forecast_link_risk(history, threshold=58)["warning"]
        if predicted and actual_failure: tp += 1
        elif predicted and not actual_failure: fp += 1
        elif not predicted and not actual_failure: tn += 1
        else: fn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    false_alarm = fp / (fp + tn) if fp + tn else 0.0
    return {
        "samples": max(1, int(samples)), "seed": seed, "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision_pct": round(precision * 100, 2), "recall_pct": round(recall * 100, 2),
        "false_alarm_rate_pct": round(false_alarm * 100, 2),
        "message": "Four prior synthetic observations predict a fifth, separately labeled observation; synthetic-only evaluation.",
    }


def simulate_cascading_failure(graph: nx.Graph, source: Any, destination: Any,
                               primary_route: list, seed: int = 42,
                               congestion_threshold: float = 92.0) -> dict[str, Any]:
    """Inject one failed route edge, reroute, shift load, and simulate overload cascades."""
    rng = random.Random(seed)
    g = graph.copy()
    timeline = []
    t0 = time.perf_counter()

    def record(name: str, detail: str, simulated_seconds: float, kind: str = "SIMULATED_EVENT"):
        timeline.append({
            "event": name,
            "detail": detail,
            "simulated_time_s": round(simulated_seconds, 3),
            "algorithm_elapsed_ms": round((time.perf_counter() - t0) * 1000, 5),
            "event_type": kind,
        })

    record("Degradation detected", "Synthetic telemetry indicates increasing link pressure.", 0.0)
    failed = tuple(primary_route[:2]) if len(primary_route) >= 2 else None
    # Prepare a backup before the failure and measure the actual algorithm work.
    backup_graph = g.copy()
    if failed and backup_graph.has_edge(*failed):
        backup_graph.remove_edge(*failed)
    start = time.perf_counter()
    backup = _safe_route(backup_graph, source, destination)
    precompute_ms = (time.perf_counter() - start) * 1000
    record("Backup prepared", f"Backup route computed in {precompute_ms:.5f} ms.", 0.05, "ALGORITHM_MEASUREMENT")

    if failed and g.has_edge(*failed):
        g.remove_edge(*failed)
        record("Link failure injected", f"Disabled synthetic link {failed[0]} ↔ {failed[1]}.", 0.10)
    else:
        record("Link failure unavailable", "No valid primary edge was available to disable.", 0.10)

    # Shift load across the alternate route. The amount is seeded and repeatable.
    route = backup
    start = time.perf_counter()
    if route:
        for u, v in zip(route, route[1:]):
            if g.has_edge(u, v):
                data = g[u][v]
                before = float(data.get("congestion_pct", 50))
                data["congestion_pct"] = min(100.0, before + rng.randint(12, 26))
                data["composite_cost"] = round(float(data.get("composite_cost", 1)) + max(0, data["congestion_pct"] - before) * 0.12, 3)
        record("Traffic rerouted", f"Adaptive route: {' → '.join(route)}. Load shifted onto backup links.", 0.15)
    else:
        record("Recovery failed", "No alternate path connects source and destination.", 0.15)
    switch_ms = (time.perf_counter() - start) * 1000
    if route:
        record("Route switch measured", f"Load shift and route activation took {switch_ms:.5f} ms of local algorithm time.", 0.16, "ALGORITHM_MEASUREMENT")

    secondary = []
    if route:
        for u, v in zip(route, route[1:]):
            if g.has_edge(u, v) and float(g[u][v].get("congestion_pct", 0)) >= congestion_threshold:
                secondary.append((u, v))
        for u, v in secondary:
            if g.has_edge(u, v):
                g.remove_edge(u, v)
        if secondary:
            record("Secondary overload failure", f"{len(secondary)} backup link(s) exceeded the {congestion_threshold:.0f}% congestion threshold and were disabled.", 0.20)
            route = _safe_route(g, source, destination)
            if route:
                record("Adaptive stabilization", f"Found a second viable route: {' → '.join(route)}.", 0.25)
            else:
                record("Network partitioned", "No source-to-destination route remains after cascading overload.", 0.25)
    if route and _valid_route(g, route, source, destination):
        record("Recovery verified", "Route endpoints and every active hop were validated.", 0.30)
    elif not any(row["event"] in {"Recovery failed", "Network partitioned"} for row in timeline):
        record("Recovery failed", "Connectivity validation failed after rerouting.", 0.30)

    return {
        "seed": seed, "failed_edge": failed, "route": route,
        "secondary_failures": secondary,
        "recovered": _valid_route(g, route, source, destination),
        "backup_precompute_ms": precompute_ms,
        "switch_ms": switch_ms,
        "route_cost": _route_cost(g, route),
        "timeline": timeline,
        "graph_after": g,
        "message": "All network events are synthetic; algorithm durations are measured locally.",
    }
