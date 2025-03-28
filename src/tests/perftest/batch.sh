#!/bin/bash

# for N in 1 10 20 30 40 50; do
# export NUM=$N
# echo "Number of workers" $N
# python req_gen_yuhan.py
# done

qps=(1 10 100 1000)
num_workers=50
input_len=(100)
output_len=(1)

for q in ${qps[@]}; do
    for i in ${input_len[@]}; do
        for o in ${output_len[@]}; do
            export QPS=$q
            export NUM=$num_workers
            export INPUT_LEN=$i
            export OUTPUT_LEN=$o
            echo "QPS: $q, Number of workers: $num_workers, Input length: $i, Output length: $o"
            python request_generator.py --qps $QPS --num-workers $NUM --duration 10 --input-len $INPUT_LEN --output-len $OUTPUT_LEN
        done
    done
done
