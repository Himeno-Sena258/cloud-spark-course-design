import argparse
import json
import re
from pathlib import Path


RESULT_PATTERN = re.compile(r"A3_RESULT_JSON=(\{.*\})")


def read_result(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    matches = RESULT_PATTERN.findall(text)
    if not matches:
        raise ValueError(f"No A3_RESULT_JSON line found in {path}")
    return json.loads(matches[-1])


def svg_chart(results: list[dict], output: Path) -> None:
    width, height = 900, 520
    left, right, top, bottom = 90, 40, 60, 100
    chart_width = width - left - right
    chart_height = height - top - bottom
    values = [item["average_seconds"] for item in results]
    maximum = max(values) * 1.15 or 1
    bar_width = chart_width / (len(results) * 2)
    gap = bar_width
    colors = ["#287D3C", "#2474B5", "#D97706"]

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="450" y="32" text-anchor="middle" font-family="Arial" '
        'font-size="22" font-weight="bold">A-3 Execution Time Comparison</text>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_height}" '
        'stroke="#333" stroke-width="2"/>',
        f'<line x1="{left}" y1="{top + chart_height}" x2="{left + chart_width}" '
        f'y2="{top + chart_height}" stroke="#333" stroke-width="2"/>',
    ]

    for tick in range(6):
        value = maximum * tick / 5
        y = top + chart_height - chart_height * tick / 5
        lines.extend(
            [
                f'<line x1="{left}" y1="{y:.1f}" x2="{left + chart_width}" y2="{y:.1f}" '
                'stroke="#ddd"/>',
                f'<text x="{left - 10}" y="{y + 5:.1f}" text-anchor="end" '
                f'font-family="Arial" font-size="13">{value:.2f}</text>',
            ]
        )

    for index, (item, value) in enumerate(zip(results, values)):
        x = left + gap + index * (bar_width + gap)
        bar_height = chart_height * value / maximum
        y = top + chart_height - bar_height
        if item["engine"] == "pandas":
            label = "Pandas"
        else:
            label = f'PySpark ({item["executors"]} executor)'
        lines.extend(
            [
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" '
                f'height="{bar_height:.1f}" fill="{colors[index]}"/>',
                f'<text x="{x + bar_width / 2:.1f}" y="{y - 10:.1f}" text-anchor="middle" '
                f'font-family="Arial" font-size="15" font-weight="bold">{value:.3f}s</text>',
                f'<text x="{x + bar_width / 2:.1f}" y="{top + chart_height + 30}" '
                f'text-anchor="middle" font-family="Arial" font-size="14">{label}</text>',
            ]
        )

    lines.extend(
        [
            '<text x="22" y="260" transform="rotate(-90 22 260)" text-anchor="middle" '
            'font-family="Arial" font-size="15">Average execution time (seconds)</text>',
            "</svg>",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pandas", type=Path, required=True)
    parser.add_argument("--spark1", type=Path, required=True)
    parser.add_argument("--spark2", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("docs/a3"))
    args = parser.parse_args()

    results = [
        read_result(args.pandas),
        read_result(args.spark1),
        read_result(args.spark2),
    ]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    pandas_time = results[0]["average_seconds"]
    for item in results:
        item["speedup_vs_pandas"] = pandas_time / item["average_seconds"]

    spark_one = results[1]["average_seconds"]
    spark_two = results[2]["average_seconds"]
    spark_speedup = spark_one / spark_two
    parallel_fraction = 2 * (1 - 1 / spark_speedup) if spark_speedup > 0 else 0
    parallel_fraction = max(0.0, min(1.0, parallel_fraction))

    summary = {
        "results": results,
        "spark_1_to_2_speedup": spark_speedup,
        "estimated_parallel_fraction": parallel_fraction,
        "amdahl_theoretical_speedup_p2": 1
        / ((1 - parallel_fraction) + parallel_fraction / 2),
    }
    (args.output_dir / "performance_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    svg_chart(results, args.output_dir / "performance_comparison.svg")

    print("=== A3 PERFORMANCE SUMMARY ===")
    for item in results:
        label = (
            "Pandas"
            if item["engine"] == "pandas"
            else f'PySpark-{item["executors"]}-executor'
        )
        print(
            f'{label}: average={item["average_seconds"]:.4f}s, '
            f'speedup_vs_pandas={item["speedup_vs_pandas"]:.4f}'
        )
    print(f"Spark 1-to-2 executor speedup: {spark_speedup:.4f}")
    print(f"Estimated parallel fraction f: {parallel_fraction:.4f}")
    print(f"Amdahl theoretical speedup at p=2: {summary['amdahl_theoretical_speedup_p2']:.4f}")


if __name__ == "__main__":
    main()
