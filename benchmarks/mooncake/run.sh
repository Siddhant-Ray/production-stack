#!/bin/bash
if [[ $# -ne 3 ]]; then
    echo "Usage: $0 <model> <base url> <save file key>"
    exit 1
fi
MODEL=$1
BASE_URL=$2
# CONFIGURATION
NUM_USERS=320
NUM_ROUNDS=5
SYSTEM_PROMPT=0 # Shared system prompt length
CHAT_HISTORY=0 # User specific chat history length
ANSWER_LEN=2000 # Generation length per round
TIME=20
MAX_QPS=5
run_benchmark() {
    # $1: qps
    # $2: output file
    # Real run
    python3 ./mooncake-qa.py \
        --num-users $NUM_USERS \
        --num-rounds $NUM_ROUNDS \
        --qps 1 \
        --shared-system-prompt "$SYSTEM_PROMPT" \
        --user-history-prompt "$CHAT_HISTORY" \
        --answer-len $ANSWER_LEN \
        --model "$MODEL" \
        --base-url "$BASE_URL" \
        --output "$2" \
        --log-interval 30 \
        --time 500 \
        --slowdown-factor $1
    sleep 10
}
KEY=$3
# Run benchmarks for different QPS values
SLOWDOWN_FACTORS=(15 10 8 6 5 2)
# Run benchmarks for the determined QPS values
for sd in "${SLOWDOWN_FACTORS[@]}"; do
    output_file="${KEY}_output_1_sd${sd}.csv"
    run_benchmark "$sd" "$output_file"
done