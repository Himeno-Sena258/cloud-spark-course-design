import argparse
import concurrent.futures
import time
import urllib.request


def request_once(url: str, timeout: float) -> tuple[bool, float]:
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            response.read()
            ok = 200 <= response.status < 300
    except Exception:
        ok = False
    return ok, time.perf_counter() - start


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple HTTP load tester for HPA verification.")
    parser.add_argument("url")
    parser.add_argument("-n", "--requests", type=int, default=10000)
    parser.add_argument("-c", "--concurrency", type=int, default=200)
    parser.add_argument("--timeout", type=float, default=5)
    args = parser.parse_args()

    started = time.perf_counter()
    ok_count = 0
    durations: list[float] = []

    print(f"URL: {args.url}")
    print(f"Total requests: {args.requests}, concurrency: {args.concurrency}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(request_once, args.url, args.timeout) for _ in range(args.requests)]
        for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
            ok, duration = future.result()
            ok_count += int(ok)
            durations.append(duration)
            if index % 500 == 0 or index == args.requests:
                elapsed = time.perf_counter() - started
                print(f"completed={index}/{args.requests} ok={ok_count} elapsed={elapsed:.1f}s")

    elapsed = time.perf_counter() - started
    failed = args.requests - ok_count
    avg = sum(durations) / len(durations) if durations else 0.0
    rps = args.requests / elapsed if elapsed > 0 else 0.0

    print("\nSummary")
    print(f"ok: {ok_count}")
    print(f"failed: {failed}")
    print(f"total time: {elapsed:.2f}s")
    print(f"requests/sec: {rps:.2f}")
    print(f"avg latency: {avg:.3f}s")


if __name__ == "__main__":
    main()
