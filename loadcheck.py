import requests
import concurrent.futures

URL = "http://localhost:5000/users"  # Port-forwarded backend

def hit():
    try:
        r = requests.get(URL, timeout=5)
        pod = r.headers.get("X-Pod-Name")
        elapsed = r.elapsed.total_seconds()
        return r.status_code, pod, elapsed
    except Exception:
        return "ERR", None, None

def main():
    total = int(input("Enter number of requests: "))
    print(f"\nSending {total} concurrent requests to backend...\n")

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(hit) for _ in range(total)]
        for f in concurrent.futures.as_completed(futures):
            status, pod, elapsed = f.result()
            results.append((status, pod, elapsed))

    # Summary
    pods_count = {}
    success = 0
    failed = 0
    total_time = 0.0
    for status, pod, elapsed in results:
        if status == 200:
            success += 1
        else:
            failed += 1
        pods_count[pod] = pods_count.get(pod, 0) + 1
        if elapsed:
            total_time += elapsed

    print("\n--- POD HIT COUNT ---")
    for pod, count in pods_count.items():
        print(f"{pod}: {count} requests")

    print(f"\nTotal Success: {success}")
    print(f"Total Failed: {failed}")
    print(f"Total Time Taken for all requests: {total_time:.3f}s")

if __name__ == "__main__":
    main()

