from concurrent.futures import ThreadPoolExecutor, as_completed


def run_parallel(tasks, max_workers=5):
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(task) for task in tasks]

        for future in as_completed(futures):
            try:
                data = future.result()
                if data:
                    results.extend(data)
            except Exception as e:
                print("Parallel task error:", e)

    return results
