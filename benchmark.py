import csv
import platform
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from models import Order
from orderbook import OrderBook

RESULTS = Path(__file__).resolve().parent / "results"
RESULTS.mkdir(exist_ok=True)


def throughput_run(pairs=5000):
    book = OrderBook()
    start = time.perf_counter()
    for i in range(pairs):
        book.submit(Order(f"S{i}", "sell", 10000, 1))
        book.submit(Order(f"B{i}", "buy", 10000, 1))
    elapsed = time.perf_counter() - start
    assert len(book.trades) == pairs
    return pairs * 2 / elapsed


def sweep_run(depth):
    book = OrderBook()
    for i in range(depth):
        book.submit(Order(f"S{i}", "sell", 10000 + i, 1))
    start = time.perf_counter_ns()
    trades = book.submit(Order("B", "buy", 10000 + depth, depth))
    elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
    assert len(trades) == depth
    return elapsed_ms


def p95(values):
    ordered = sorted(values)
    return ordered[(95 * len(ordered) + 99) // 100 - 1]


def main():
    throughput_run(500)
    speed_samples = [throughput_run() for _ in range(5)]
    speed = statistics.median(speed_samples)
    depths = (10, 100, 500, 1000, 2000)
    rows = []
    for depth in depths:
        sweep_run(depth)
        times = [sweep_run(depth) for _ in range(15)]
        rows.append((depth, statistics.median(times), p95(times)))

    with (RESULTS / "benchmark_latency.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(("resting_orders", "median_full_fill_ms", "p95_full_fill_ms"))
        for depth, median_ms, p95_ms in rows:
            writer.writerow((depth, f"{median_ms:.4f}", f"{p95_ms:.4f}"))

    lines = [
        "# Performance benchmark",
        "",
        f"Run: {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}",
        f"Python: {platform.python_version()}",
        f"OS: {platform.platform()}",
        "",
        "## Alternating buy/sell submissions",
        f"**{speed:,.0f} orders/sec** (median of 5 runs; 5,000 sell/buy pairs per run).",
        "",
        "## Full-order fill time",
        "",
        "| Resting asks / trades filled | Median (ms) | p95 (ms) |",
        "|---:|---:|---:|",
    ]
    for depth, median_ms, p95_ms in rows:
        lines.append(f"| {depth:,} | {median_ms:.4f} | {p95_ms:.4f} |")
    lines.extend([
        "",
        "Benchmarks use synthetic, in-memory orders on one Python process.",
        "The full-fill timer excludes book setup and includes all fills for one incoming buy order.",
        "The throughput test alternates a one-unit sell and an immediately matching buy; it is a simple best-case workload.",
        "No network, persistence, fees, or production exchange infrastructure are included.",
        "Numbers depend on hardware and background load; not suitable for comparing exchange systems.",
        "",
        "![Full-fill scaling](benchmark_scaling.png)",
        "",
    ])
    (RESULTS / "benchmark_results.md").write_text("\n".join(lines), encoding="utf-8")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot([x[0] for x in rows], [x[1] for x in rows], marker="o", linewidth=2)
        ax.set(xlabel="Resting ask orders", ylabel="Full fill time (ms)", title="Order Book: Full Fill Latency")
        ax.grid(alpha=0.25)
        fig.tight_layout()
        fig.savefig(RESULTS / "benchmark_scaling.png", dpi=170)
        plt.close(fig)
    except ImportError:
        lines = [line for line in lines if "benchmark_scaling.png" not in line]
        (RESULTS / "benchmark_results.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Throughput: {speed:,.0f} orders/sec")
    for depth, median_ms, p95_ms in rows:
        print(f"{depth:>4} fills: median {median_ms:.3f} ms | p95 {p95_ms:.3f} ms")
    print("Saved to results/benchmark_results.md")


if __name__ == "__main__":
    main()
