from collections import defaultdict
import json, os
import time, datetime as dt
import pandas as pd

from collections import defaultdict

class TrieNode:
    def __init__(self):
        self.children = defaultdict(TrieNode)
        self.count = 0
        self.sequence_indices = []

class PrefixTrie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, sequence, index):
        node = self.root
        for num in sequence:
            node = node.children[num]
            node.count += 1
            node.sequence_indices.append(index)

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
                min_idx = min(node.sequence_indices)
                max_idx = max(node.sequence_indices)
                spread = max_idx - min_idx
                results.append({
                    "prefix": path[:],
                    "count": node.count,
                    "indices": node.sequence_indices[:],
                    "spread": spread
                })
            for num, child in node.children.items():
                path.append(num)
                dfs(child, path)
                path.pop()

        dfs(self.root, [])
        return results
    

file_path = "./Mooncake/mooncake_trace.jsonl"
count = 0
mooncake_sequences = {}
with open(file_path, "r") as f:
    lines = f.readlines()
    for line in lines:
        line = json.loads(line)
        key = count
        input_length = line["input_length"]
        output_length = line["output_length"]
        hash_ids = line["hash_ids"]
        mooncake_sequences[key] = {
            "input_length": input_length,
            "output_length": output_length,
            "hash_ids": hash_ids
        }
        count += 1

prefix_lists = []
for key, value in mooncake_sequences.items():
    hash_ids = value["hash_ids"]
    prefix_lists.append(hash_ids)

if not os.path.exists("shared_prefixes.csv"):
    trie = PrefixTrie()
    for i, seq in enumerate(prefix_lists, start = 1):
        trie.insert(seq, i)

    shared = trie.all_shared_prefixes()

    with open("shared_prefixes.csv", "w") as f:
        for item in shared:
            # f.write(f"Prefix; {item['prefix']}; shared by;  {item['count']} sequences; indices; {item['indices']}; spread; {item['spread']}\n")
            f.write(f"{item['prefix']}; {item['count']}; {item['indices']}; {item['spread']}\n")


df = pd.read_csv("shared_prefixes.csv", sep=";")
df.columns = ["Prefix", "Count", "Indices", "Spread"]

# sort by count
df = df.sort_values(by="Count", ascending=False, ignore_index=True)
print(df.head(10))