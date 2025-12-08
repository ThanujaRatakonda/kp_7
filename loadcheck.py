import requests
import concurrent.futures
URL = "http://10.131.103.92:4000"
def hit():
    try:
        r = requests.get(URL, timeout=5)
        return r.status_code, r.headers.get("X-Pod-Name"), r.elapsed.total_seconds()
    except Exception as e:
        return "ERR", None, None
def main():
    total = 50
    print(f"Sending concurrent requests...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5000) as executor:
        results = list(executor.map(lambda _: hit(), range(total)))

    ok = sum(1 for r in results if r[0] == 200)
    fail = sum(1 for r in results if r[0] != 200)

    print("\n--- RESULT SUMMARY ---")
    print(f"Success: {ok}")
    print(f"Failed: {fail}")

    print("\nPod distribution:")
    pods = {}
    for _, pod, _ in results:
        if pod:
            pods[pod] = pods.get(pod, 0) + 1
    for p, count in pods.items():
        print(f"{p}: {count} requests")
if __name__ == "__main__":
    main()
