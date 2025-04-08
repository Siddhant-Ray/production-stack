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
        self.insertion_index = 1

    def insert(self, sequence, meta):

        meta_with_index = dict(meta)
        meta_with_index["insertion_index"] = self.insertion_index
        self.insertion_index += 1

        node = self.root
        for num in sequence:
            node = node.children[num]
            node.count += 1
            node.metadata.append(meta_with_index)

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
                indices = [m['insertion_index'] for m in node.metadata]
                indices.sort()

                # Calculate spread
                spread = indices[-1] - indices[0] if indices else 0

                # Calculate shortest distance between consecutive occurrences
                next_diff = float("inf")
                for i in range(1, len(indices)):
                    diff = indices[i] - indices[i - 1]
                    if diff < next_diff:
                        next_diff = diff
                next_diff = next_diff if next_diff != float("inf") else None

                results.append({
                    "prefix": path[:],
                    "count": node.count,
                    "repeat": indices[:],
                    "next": next_diff,
                    "metadata": node.metadata[:],
                    "spread": spread
                })
            for num, child in node.children.items():
                path.append(num)
                dfs(child, path)
                path.pop()

        dfs(self.root, [])

        return results

file_path = "./conversation_trace_copy_copy.jsonl"
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
                "spread": item["spread"],
                "next": item["next"],
                "repeat": item["repeat"],
                "count": len(item["repeat"]),
            })

    df = pd.DataFrame(rows)
    df.to_csv("shared_prefixes_full.csv", index=False, sep=";")

df = pd.read_csv("shared_prefixes_full.csv", sep=";")
df.columns = ["timestamp", "input_length", "output_length", "hash_ids", "prefix", "spread", "next", "repeat", "count"]

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

# If repeat values are the same, find the overlap between the
# hash ids of the those repeat values and divide by the number 
# of hash ids in the first repeat value,
# multiply by 100 to get a percentage

# first group by repeat values and then find the overlap
# of the corresponding hash id lists

# convert hash_ids column to a list

df["hash_ids"] = df["hash_ids"].apply(lambda x: eval(x))

df["fraction"] = df.apply(
    lambda row: len(set(row["hash_ids"]).intersection(
        set(df[df["repeat"] == row["repeat"]]["hash_ids"].values[0])
    )) / len(row["hash_ids"]) * 100
    if len(row["hash_ids"]) > 0 else 0,
    axis=1
)

# sort by fraction
df = df.sort_values(by=["fraction"], ascending=[False], ignore_index=True)

# Group by repeat values and for all fractions in the group,
# make the first fraction 0, keep the rest of the fractions same

def set_one_fraction_zero(group):
    if len(group) >= 1:
        group.loc[group.index[0], "fraction"] = 0  # Set the first one to 0
    return group

df = df.groupby("repeat", group_keys=False).apply(set_one_fraction_zero)

# sort by repeat values
df = df.sort_values(by=["repeat", "fraction"], ascending=[False, True], ignore_index=True)


print(df.head(10))


# print(df.head(30))

print(df.head(31))

# Keep prefix lengths that are less than 50
# df = df[df["prefix_len"] > 5]
# number of unique repeat values is number os sessions
# unique_repeats = df["repeat"].nunique()
# print(f"Number of unique repeat values: {unique_repeats}")

# print first row , prefix value
# print(df.iloc[0]["prefix"])
# print(len(df.iloc[0]["prefix"]))



# plot prefix length vs count
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# plot distribution of fraction
plt.figure(figsize=(10, 6))
# plot ecdf of fraction
sns.ecdfplot(df["fraction"], stat="proportion")
plt.xlabel("Fraction of hash ids in the prefix")
plt.ylabel("Proportion")
plt.title("ECDF of Fraction of Hash IDs in the Prefix")
plt.savefig("fraction_ecdf.pdf", bbox_inches="tight")

# print distriubtion of count (prefix repeat values)
plt.figure(figsize=(10, 6))
# normali by unique repeat values
sns.histplot(df["count"], bins=30, kde=True)
plt.xlabel("Count (number of repeated prefixes)")
plt.ylabel("Count")
plt.title("Distribution Count of Shared Prefixes")
plt.savefig("prefix_count_distribution.pdf", bbox_inches="tight")

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
