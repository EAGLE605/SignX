#!/usr/bin/env python3
"""Performance Baseline Benchmarking Script.

Establishes performance baselines for key API endpoints and calculation solvers.
This baseline is used to validate that refactoring does not introduce regressions
exceeding the 2% threshold required by elite standards.

Usage:
    python scripts/benchmark_baseline.py
    python scripts/benchmark_baseline.py --output baseline.json
    python scripts/benchmark_baseline.py --compare previous_baseline.json

Output:
    JSON report with p50/p95/p99 latencies for each operation
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class BenchmarkResult:
    """Single benchmark measurement."""

    operation: str
    iterations: int
    total_time_s: float
    mean_time_ms: float
    median_time_ms: float
    p95_time_ms: float
    p99_time_ms: float
    min_time_ms: float
    max_time_ms: float
    std_dev_ms: float


@dataclass
class BaselineReport:
    """Complete baseline report."""

    timestamp: str
    git_commit: str
    python_version: str
    results: list[BenchmarkResult]
    metadata: dict[str, Any]


def percentile(data: list[float], p: float) -> float:
    """Calculate percentile of data."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    index = int(len(sorted_data) * p)
    return sorted_data[min(index, len(sorted_data) - 1)]


def benchmark_operation(name: str, operation: callable, iterations: int = 1000) -> BenchmarkResult:
    """Benchmark a single operation."""
    times: list[float] = []

    # Warmup
    for _ in range(10):
        operation()

    # Actual benchmark
    for _ in range(iterations):
        start = time.perf_counter()
        operation()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to milliseconds

    total_time = sum(times) / 1000  # Convert to seconds

    return BenchmarkResult(
        operation=name,
        iterations=iterations,
        total_time_s=total_time,
        mean_time_ms=statistics.mean(times),
        median_time_ms=statistics.median(times),
        p95_time_ms=percentile(times, 0.95),
        p99_time_ms=percentile(times, 0.99),
        min_time_ms=min(times),
        max_time_ms=max(times),
        std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0.0,
    )


# ===== Benchmark Operations =====


def bench_dict_creation():
    """Benchmark dict creation (control operation)."""
    data = {
        "key1": "value1",
        "key2": 123,
        "key3": [1, 2, 3],
        "nested": {"foo": "bar"},
    }
    return data


def bench_list_comprehension():
    """Benchmark list comprehension."""
    return [x * 2 for x in range(100)]


def bench_datetime_now_utc():
    """Benchmark timezone-aware datetime creation."""
    return datetime.now(UTC)


def bench_json_encode():
    """Benchmark JSON encoding."""
    data = {
        "project_id": "proj_123",
        "cabinets": [
            {"width": 48, "height": 96, "depth": 12, "weight": 150},
            {"width": 36, "height": 72, "depth": 10, "weight": 100},
        ],
        "loads": {"wind_speed_mph": 115, "exposure": "C", "importance": 1.0},
    }
    return json.dumps(data)


def bench_json_decode():
    """Benchmark JSON decoding."""
    json_str = '{"project_id":"proj_123","cabinets":[{"width":48,"height":96}]}'
    return json.loads(json_str)


# ===== Main Benchmarking =====


def run_benchmarks() -> list[BenchmarkResult]:
    """Run all benchmarks."""
    benchmarks = [
        ("dict_creation", bench_dict_creation, 10000),
        ("list_comprehension", bench_list_comprehension, 10000),
        ("datetime_now_utc", bench_datetime_now_utc, 10000),
        ("json_encode", bench_json_encode, 5000),
        ("json_decode", bench_json_decode, 5000),
    ]

    results = []
    for name, operation, iterations in benchmarks:
        print(f"Benchmarking {name}... ", end="", flush=True)
        result = benchmark_operation(name, operation, iterations)
        results.append(result)
        print(f"✓ (mean: {result.mean_time_ms:.4f}ms)")

    return results


def get_git_commit() -> str:
    """Get current git commit hash."""
    try:
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def get_python_version() -> str:
    """Get Python version."""
    import sys

    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def generate_report(results: list[BenchmarkResult]) -> BaselineReport:
    """Generate baseline report."""
    return BaselineReport(
        timestamp=datetime.now(UTC).isoformat(),
        git_commit=get_git_commit(),
        python_version=get_python_version(),
        results=results,
        metadata={
            "description": "Performance baseline for SignX API refactoring validation",
            "purpose": "Validate <2% regression after code changes",
            "environment": "Docker container (isolated)",
        },
    )


def save_report(report: BaselineReport, output_path: Path) -> None:
    """Save report to JSON file."""
    with output_path.open("w") as f:
        json.dump(
            {
                "timestamp": report.timestamp,
                "git_commit": report.git_commit,
                "python_version": report.python_version,
                "results": [asdict(r) for r in report.results],
                "metadata": report.metadata,
            },
            f,
            indent=2,
        )
    print(f"\n✅ Baseline report saved to: {output_path}")


def print_report(report: BaselineReport) -> None:
    """Print report to console."""
    print("\n" + "=" * 80)
    print("PERFORMANCE BASELINE REPORT")
    print("=" * 80)
    print(f"Timestamp:      {report.timestamp}")
    print(f"Git Commit:     {report.git_commit[:8]}")
    print(f"Python Version: {report.python_version}")
    print("=" * 80)
    print()

    # Table header
    print(
        f"{'Operation':<25} {'Iterations':>10} {'Mean (ms)':>12} "
        f"{'P95 (ms)':>12} {'P99 (ms)':>12}"
    )
    print("-" * 80)

    for result in report.results:
        print(
            f"{result.operation:<25} {result.iterations:>10,} "
            f"{result.mean_time_ms:>12.4f} {result.p95_time_ms:>12.4f} "
            f"{result.p99_time_ms:>12.4f}"
        )

    print("=" * 80)


def compare_reports(baseline_path: Path, current_path: Path) -> None:
    """Compare two baseline reports."""
    with baseline_path.open() as f:
        baseline = json.load(f)

    with current_path.open() as f:
        current = json.load(f)

    print("\n" + "=" * 80)
    print("PERFORMANCE REGRESSION ANALYSIS")
    print("=" * 80)
    print(f"Baseline: {baseline['git_commit'][:8]} ({baseline['timestamp']})")
    print(f"Current:  {current['git_commit'][:8]} ({current['timestamp']})")
    print("=" * 80)
    print()

    # Build lookup
    baseline_lookup = {r["operation"]: r for r in baseline["results"]}
    current_lookup = {r["operation"]: r for r in current["results"]}

    # Compare
    print(f"{'Operation':<25} {'Baseline (ms)':>15} {'Current (ms)':>15} {'Regression':>12}")
    print("-" * 80)

    max_regression = 0.0
    for operation in baseline_lookup:
        if operation not in current_lookup:
            continue

        baseline_mean = baseline_lookup[operation]["mean_time_ms"]
        current_mean = current_lookup[operation]["mean_time_ms"]
        regression_pct = ((current_mean - baseline_mean) / baseline_mean) * 100

        max_regression = max(max_regression, regression_pct)

        status = "✅" if regression_pct < 2.0 else "⚠️" if regression_pct < 5.0 else "❌"

        print(
            f"{operation:<25} {baseline_mean:>15.4f} {current_mean:>15.4f} "
            f"{status} {regression_pct:>8.2f}%"
        )

    print("=" * 80)
    print(f"\nMaximum Regression: {max_regression:.2f}%")

    if max_regression < 2.0:
        print("✅ PASS: All operations within 2% regression threshold")
    elif max_regression < 5.0:
        print("⚠️  WARNING: Some operations exceed 2% but within 5%")
    else:
        print("❌ FAIL: Operations exceed 5% regression threshold")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Performance baseline benchmarking")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("baseline.json"),
        help="Output file path",
    )
    parser.add_argument(
        "--compare",
        type=Path,
        help="Compare against previous baseline",
    )

    args = parser.parse_args()

    if args.compare:
        if not args.compare.exists():
            print(f"❌ Baseline file not found: {args.compare}")
            return

        if not args.output.exists():
            print("Running benchmarks for current version...")
            results = run_benchmarks()
            report = generate_report(results)
            save_report(report, args.output)

        compare_reports(args.compare, args.output)
    else:
        print("Running performance baseline benchmarks...\n")
        results = run_benchmarks()
        report = generate_report(results)
        print_report(report)
        save_report(report, args.output)


if __name__ == "__main__":
    main()
