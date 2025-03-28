import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

results_dir_1 = "results_conc_prod/results_conc_10000_1000"

for file in os.listdir(results_dir_1):
    print(
        f"results for {results_dir_1.split("_")[2]} input and {results_dir_1.split("_")[3]} output"
    )
    if file.endswith(".csv"):
        if file.startswith("50"):
            second_place = float(file.split("_")[1])
            df = pd.read_csv(
                os.path.join(results_dir_1, file),
                sep=";",
                names=["length", "time", "tpt", "input_speed", "ttft"],
            )

            print(f"Mean ttft for {second_place} qps: {df['ttft'].mean()}")
            print(
                f"Mean input speed for {second_place} qps: {df['input_speed'].mean()}"
            )
            print(f"Mean throughput for {second_place} qps: {df['tpt'].mean()}")

    print("\n")
