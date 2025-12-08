import requests
import concurrent.futures

URL = "http://10.131.103.92:5000/users" 

def hit():
    try:
        r = requests.get(URL, timeout=5)
        return r.status_code, r.elapsed.total_seconds()
    except Exception:
        return "ERR", None

def main():
    total_requests = 500
    print(f"Sending {total_requests} concurrent requests...")

    # ThreadPoolExecutor to run requests concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=500) as executor:
        results = list(executor.map(lambda _: hit(), range(total_requests)))

    success = sum(1 for r in results if r[0] == 200)
    failed = sum(1 for r in results if r[0] != 200)

    print("\n--- RESULT SUMMARY ---")
    print(f"Success: {success}")
    print(f"Failed: {failed}")

if __name__ == "__main__":
    main()

