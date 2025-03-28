import argparse
import multiprocessing
import os
import threading
import time
import uuid

import openai


def response_consumer(
    response_stream, start_time, file, lock, input_len, output_len, concurrent_requests
):
    chunk_messages = []
    token_time = None
    try:
        for tok in response_stream:
            if not tok.choices:
                continue
            chunk_message = tok.choices[0].delta.content
            if chunk_message is not None:
                if token_time is None:
                    token_time = time.time()
                chunk_messages.append(chunk_message)
    except Exception as e:
        print(
            f"Error in consumer thread {threading.current_thread().name} of process {os.getpid()}: {e}"
        )
    final_words = "".join(chunk_messages)
    end_time = time.time()
    response_len = len(final_words.split(" "))
    throughput = response_len / (end_time - start_time)
    # input_speed = input_len / (token_time - start_time)

    # input speed is input_len * number of concurrent requests
    input_speed = input_len * concurrent_requests.value
    output_speed = response_len * concurrent_requests.value

    lock.acquire()
    with open(file, "a") as f:
        f.write(
            f"{response_len};{end_time-start_time};{output_speed};{input_speed};{token_time-start_time}\n"
        )
    lock.release()

    # Decrement concurrent request count after response is fully processed
    with concurrent_requests.get_lock():
        concurrent_requests.value -= 1

    print(
        f"Process {os.getpid()} got a response of: {response_len} words in {end_time-start_time:.2f} seconds (throughput: {throughput:.2f} w/s, ttft: {token_time - start_time:.4f}) at {end_time}"
    )


def worker(
    api_key,
    base_url,
    model,
    qps_per_worker,
    file,
    lock,
    global_start,
    duration,
    input_len,
    output_len,
    concurrent_requests,
):
    client = openai.OpenAI(api_key=api_key, base_url=base_url)
    interval = 1 / qps_per_worker

    while True:
        start = time.time()
        # print("Send request at ", start)
        try:
            request_id = str(uuid.uuid4())
            custom_headers = {
                "x-user-id": str(os.getpid()),  # Unique user ID for each process
                "x-request-id": str(os.getpid())
                + f"req-{request_id}",  # Unique session ID for each process
            }

            # Increment concurrent request count before sending the request
            with concurrent_requests.get_lock():
                concurrent_requests.value += 1

            response_stream = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": "Hi" * input_len,
                    }
                ],
                model=model,
                temperature=0,
                stream=True,
                max_tokens=output_len,
                extra_headers=custom_headers,
            )
            start_time = time.time()
            print(
                "Process {} sent a request at {:.4f}, connection overhead: {:.4f}".format(
                    os.getpid(), start_time, start_time - start
                )
            )

            consumer_thread = threading.Thread(
                target=response_consumer,
                args=(
                    response_stream,
                    start,
                    file,
                    lock,
                    input_len,
                    output_len,
                    concurrent_requests,
                ),
                daemon=True,
            )
            consumer_thread.start()
        except Exception as e:
            print(f"Error in process {os.getpid()}: {e}")

            # If request fails, decrement the counter
            with concurrent_requests.get_lock():
                concurrent_requests.value -= 1

        elapsed = time.time() - start

        # Exit if duation is reached
        if time.time() - global_start > duration:
            exit(0)

        if elapsed < interval:
            time.sleep(interval - elapsed)
        else:
            print("WARNING: Process {} is too slow".format(os.getpid()))


def main():
    parser = argparse.ArgumentParser(description="Stress test an OpenAI API server")
    parser.add_argument(
        "--qps", type=float, required=True, help="Total queries per second"
    )
    parser.add_argument(
        "--num-workers", type=int, required=True, help="Number of worker processes"
    )
    parser.add_argument(
        "--duration", type=int, default=60, help="Duration of the test in seconds"
    )
    parser.add_argument(
        "--input-len", type=int, default=100, help="Length of input message"
    )
    parser.add_argument(
        "--output-len", type=int, default=1000, help="Length of output message"
    )

    args = parser.parse_args()
    qps_per_worker = args.qps / args.num_workers
    lock = multiprocessing.Lock()

    input_len = args.input_len
    output_len = args.output_len

    os.makedirs(f"results_conc_{input_len}_{output_len}", exist_ok=True)
    file_name = f"results_conc_{input_len}_{output_len}/{args.num_workers}_{args.qps}_{args.duration}.csv"

    processes = []
    api_key = "YOUR_API_KEY_HERE"
    base_url = "http://localhost:30080/v1"
    # model = "HuggingFaceTB/SmolLM2-135M-Instruct"
    model = "smol-135"

    global_start_time = time.time()
    concurrent_requests = multiprocessing.Value(
        "i", 0
    )  # Shared counter for concurrent requests

    for _ in range(args.num_workers):
        p = multiprocessing.Process(
            target=worker,
            args=(
                api_key,
                base_url,
                model,
                qps_per_worker,
                file_name,
                lock,
                global_start_time,
                args.duration,
                input_len,
                output_len,
                concurrent_requests,
            ),
        )
        p.start()
        processes.append(p)

    for p in processes:
        p.join()


if __name__ == "__main__":
    main()
