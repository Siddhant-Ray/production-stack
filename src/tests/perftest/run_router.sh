#!/bin/bash/

vllm-router --port 30080 \
    --service-discovery static \
    --static-backends "http://localhost:10000,http://localhost:10001,http://localhost:10002,http://localhost:10003" \
    --static-models "HuggingFaceTB/SmolLM2-135M-Instruct,HuggingFaceTB/SmolLM2-135M-Instruct,HuggingFaceTB/SmolLM2-135M-Instruct,HuggingFaceTB/SmolLM2-135M-Instruct" \
    --engine-stats-interval 10 \
    --log-stats \
    --routing-logic roundrobin
