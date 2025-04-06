import json
# Read in the data from conversation_trace.jsonl
mooncake_data = []
with open("conversation_trace.jsonl", "r") as file:
    for line in file:
        line = line.strip()
        if line:  # Skip empty lines
            try:
                record = json.loads(line)
                mooncake_data.append(record)
            except json.JSONDecodeError as e:
                print(f"Error parsing line: {line}\nError: {e}")
# Define the overall time range, window length, and sliding step (all in milliseconds)
total_start = 0
total_end = 600000  # Only consider timestamps in [0,600000)
window_length = 100000
step = 10000
# Prepare a list to hold the results for each window.
# Each result is a tuple: (window_start, window_end, diff, chunk_count, ratio)
window_results = []
# Slide the window over the specified range.
# For each window, the baseline is computed as the maximum hash id from all records before the window start.
for window_start in range(total_start, total_end - window_length + 1, step):
    window_end = window_start + window_length
    # Collect hash_ids from records with timestamp < window_start (baseline)
    baseline_hash_ids = []
    for record in mooncake_data:
        if record["timestamp"] < window_start:
            baseline_hash_ids.extend(record["hash_ids"])
    # Only process the window if there is a baseline available.
    if not baseline_hash_ids:
        continue  # Skip this window if no prior data exists
    baseline = max(baseline_hash_ids)
    # Collect hash_ids for the current window [window_start, window_end)
    window_hash_ids = []
    for record in mooncake_data:
        if window_start <= record["timestamp"] < window_end:
            window_hash_ids.extend(record["hash_ids"])
    # Only compute if we have data in the window.
    if not window_hash_ids:
        continue
    current_max = max(window_hash_ids)
    diff = current_max - baseline
    chunk_count = len(window_hash_ids)
    ratio = diff / chunk_count
    window_results.append((window_start, window_end, diff, chunk_count, ratio))
# Sort windows by the ratio in ascending order (lowest ratio first)
window_results.sort(key=lambda x: x[4])
# Print the top ten windows with the lowest ratio (diff / count).
print("Top 10 windows (from lowest to highest ratio = diff / count):")
for i, (start, end, diff, count, ratio) in enumerate(window_results[:10], start=1):
    print(f"{i}. Window [{start}, {end}): diff = {diff}, chunk count = {count}, ratio = {ratio:.4f}")