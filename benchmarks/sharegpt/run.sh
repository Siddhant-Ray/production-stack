#!/bin/bash
if [[ $# -ne 3 ]]; then
    echo "Usage: $0 <model> <base url> <save file key>"
    exit 1
fi
MODEL=$1
BASE_URL=$2
# CONFIGURATION
NUM_USERS=80
NUM_ROUNDS=20
SYSTEM_PROMPT=0 # Shared system prompt length
CHAT_HISTORY=0 # User specific chat history length
ANSWER_LEN=2000 # Generation length per round
TIME=200
MAX_QPS=3
warmup() {
    # Warm up the vLLM with a lot of user queries
    python3 ./multi-round-qa.py \
        --num-users $NUM_USERS \
        --num-rounds $NUM_ROUNDS \
        --qps $MAX_QPS \
        --shared-system-prompt $SYSTEM_PROMPT \
        --user-history-prompt $CHAT_HISTORY \
        --answer-len $ANSWER_LEN \
        --model "$MODEL" \
        --base-url "$BASE_URL" \
        --output /tmp/warmup.csv \
        --log-interval 30 \
        --time $TIME \
        --sharegpt
}
warmup
run_benchmark() {
    # $1: qps
    # $2: output file
    # Real run
    python3 ./multi-round-qa.py \
        --num-users $NUM_USERS \
        --num-rounds $NUM_ROUNDS \
        --qps "$1" \
        --shared-system-prompt "$SYSTEM_PROMPT" \
        --user-history-prompt "$CHAT_HISTORY" \
        --answer-len $ANSWER_LEN \
        --model "$MODEL" \
        --base-url "$BASE_URL" \
        --output "$2" \
        --log-interval 30 \
        --time $TIME \
        --sharegpt
    sleep 10
}
KEY=$3
# Run benchmarks for different QPS values
QPS_VALUES=(2.5 2 1.7 1.5 1.3 1 0.7 0.5 0.3)
# Run benchmarks for the determined QPS values
for qps in "${QPS_VALUES[@]}"; do
    output_file="${KEY}_output_${qps}.csv"
    run_benchmark "$qps" "$output_file"
done