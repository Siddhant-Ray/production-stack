from collections import defaultdict
import json, os
import pandas as pd

class TrieNode:
    def __init__(self):
        self.children = defaultdict(TrieNode)
        self.count = 0
        self.metadata = []  # Store dicts with full metadata

class PrefixTrie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, sequence, meta):
        node = self.root
        for num in sequence:
            node = node.children[num]
            node.count += 1
            node.metadata.append(meta)

    def get_shared_prefix_lengths(self, sequence):
        node = self.root
        shared_length = 0
        for num in sequence:
            if num in node.children:
                node = node.children[num]
                shared_length += 1
            else:
                break
        return shared_length

    def all_shared_prefixes(self):
        results = []

        def dfs(node, path):
            if node.count > 1:
                timestamps = [m['timestamp'] for m in node.metadata]
                spread = max(timestamps) - min(timestamps) if timestamps else 0
                results.append({
                    "prefix": path[:],
                    "count": node.count,
                    "metadata": node.metadata[:],
                    "spread": spread
                })
            for num, child in node.children.items():
                path.append(num)
                dfs(child, path)
                path.pop()

        dfs(self.root, [])

        # # Filter to keep only longest prefixes
        # longest_only = []
        # results.sort(key=lambda x: len(x["prefix"]), reverse=True)  # Start from longest
        # seen = set()

        # for item in results:
        #     tup_prefix = tuple(item["prefix"])
        #     if not any(tup_prefix[:i] in seen for i in range(1, len(tup_prefix))):
        #         longest_only.append(item)
        #         seen.add(tup_prefix)

        # return longest_only
        return results

file_path = "./conversation_trace.jsonl"
count = 0
mooncake_sequences = []
with open(file_path, "r") as f:
    lines = f.readlines()
    for line in lines:
        line = json.loads(line)
        key = count
        input_length = line["input_length"]
        output_length = line["output_length"]
        timestamp = line["timestamp"]
        hash_ids = line["hash_ids"]
        mooncake_sequences.append(
            {   
                "timestamp": timestamp,
                "input_length": input_length,
                "output_length": output_length, 
                "hash_ids": hash_ids
            }
        )
        count += 1

if not os.path.exists("shared_prefixes_full.csv"):

    trie = PrefixTrie()

    for entry in mooncake_sequences:
        trie.insert(entry["hash_ids"], {
            "timestamp": entry["timestamp"],
            "input_length": entry["input_length"],
            "output_length": entry["output_length"],
            "hash_ids": entry["hash_ids"],
        })

    # Get all shared prefixes
    shared_prefixes = trie.all_shared_prefixes()

    # print("Shared Prefixes:")
    # for prefix in shared_prefixes:
    #     print(f"Prefix: {prefix['prefix']}, Count: {prefix['count']}, Spread: {prefix['spread']}")

    # for item in shared_prefixes:
    #     prefix = item["prefix"]
    #     print(f"Prefix: {prefix}, Count: {item['count']}, Spread: {item['spread']}")
    # exit()

    rows = []

    for item in shared_prefixes:
        prefix = item["prefix"]
        for meta in item["metadata"]:
            rows.append({
                "timestamp": meta["timestamp"],
                "input_length": meta["input_length"],
                "output_length": meta["output_length"],
                "hash_ids": meta["hash_ids"],
                "prefix": prefix,
                "spread": item["spread"]
            })

    df = pd.DataFrame(rows)
    df.to_csv("shared_prefixes_full.csv", index=False, sep=";")

df = pd.read_csv("shared_prefixes_full.csv", sep=";")
df.columns = ["timestamp", "input_length", "output_length", "hash_ids", "prefix", "spread"]

# sort by prefix length
# make prefix a list, instead of a string of list
# df["prefix"] = df["prefix"].apply(lambda x: eval(x))
df["prefix_len"] = df["prefix"].apply(len)
# Sort by prefix length (descending) so longest prefix comes first
df = df.sort_values(by=["prefix_len"], ascending=[False], ignore_index=True)

# # # across prefixes, drop duplicates, keep the one with the longest prefix
df = df.drop_duplicates(subset=["timestamp", "input_length", "output_length", "hash_ids"], keep="first")

# print(df.head(10))

# calcualte the number of input_len values which share the same prefix
df["input_len_count"] = df.groupby("prefix")["input_length"].transform("count")

# Calculate total number of entries in the DataFrame
total_entries = len(df)
print(f"Total number of entries in the DataFrame: {total_entries}")

# make prefix a list, instead of a string of list
df["prefix"] = df["prefix"].apply(lambda x: eval(x))

# replace prefix_len column with new prefix_len column
df["prefix_len"] = df["prefix"].apply(len)

print(df.head(10))



# print first row , prefix value
print(df.iloc[0]["prefix"])
print(len(df.iloc[0]["prefix"]))

# plot prefix length vs count
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

plt.figure(figsize=(10, 6))
sns.histplot(df["prefix_len"], bins=30, kde=True)
plt.xlabel("Prefix Length (number of input ids)")
plt.ylabel("Count")
plt.title("Distribution Count of Shared Prefix Lengths")
plt.savefig("prefix_length_distribution.pdf", bbox_inches="tight")

# Print prefix length vs input length count

fractions = []
for idx, value in enumerate(df["prefix_len"]):
    fractions.append((value * 512) / df.iloc[idx]["input_length"])
    
# df_sampled = (
#     df.groupby("prefix", group_keys=False)
#     .apply(lambda x: x.sample(frac=0.2, random_state=42))
# )

# # Optional: Reset index if needed
# df_sampled.reset_index(drop=True, inplace=True)

# # sort by timestamp
# df_sampled = df_sampled.sort_values(by="timestamp", ascending=True, ignore_index=True)

# # # If timestamp, input length, output length, hash ids are same 
# # # across prefixes, drop duplicates, keep the one with the longest prefix
# # df_sampled = df_sampled.drop_duplicates(subset=["timestamp", "input_length", "output_length", "hash_ids"], keep="last")

# df_sampled["prefix_len"] = df_sampled["prefix"].apply(len)

# # Sort by prefix length (descending) so longest prefix comes first
# df_sampled = df_sampled.sort_values(by=["timestamp", "input_length", "output_length", "hash_ids", "prefix_len"], 
#             ascending=[True, True, True, True, False], ignore_index=True)

# # Drop duplicates across the core fields, keeping the longest prefix
# df_sampled = df_sampled.drop_duplicates(subset=["timestamp", "input_length", "output_length"], keep="first")
# df_sampled = df_sampled.drop(columns=["prefix_len"])

# # sort by timestamp
# df_sampled = df_sampled.sort_values(by="timestamp", ascending=True, ignore_index=True)

# # Save to CSV if needed
# df_sampled.to_csv("shared_prefixes_sampled.csv", index=False, sep=";")

# # Make the row of hash ids a list instead of a string "list"
# df_sampled["hash_ids"] = df_sampled["hash_ids"].apply(lambda x: eval(x))

# # Convert back to JSONL format after dropping the prefix column
# dropped_df = df_sampled.drop(columns=["prefix"])
# dropped_df.to_json("shared_prefixes_sampled.jsonl", orient="records", lines=True)
