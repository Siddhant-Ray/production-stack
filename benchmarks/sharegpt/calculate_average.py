import json
def compute_average_token_counts(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    # If the JSON file is a single entry, wrap it in a list
    if not isinstance(data, list):
        data = [data]
    overall_averages = []
    for entry in data:
        avg_human = entry.get("average_human_token", 0)
        avg_gpt = entry.get("average_gpt_token", 0)
        entry_average = (avg_human + avg_gpt) / 2
        overall_averages.append(entry_average)
        print(f"Entry {entry.get('id', 'unknown')} average token: {entry_average}")
    # Optionally, compute the overall average of all entries
    if overall_averages:
        overall_average = sum(overall_averages) / len(overall_averages)
        print(f"\nOverall average token across all entries: {overall_average}")
# Replace 'entries.json' with the path to your JSON file
compute_average_token_counts('/home/ubuntu/st-prodstack-i/production-stack/benchmarks/multi-round-qa/ShareGPT.json')