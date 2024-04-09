#!/bin/bash
# Set the variables

export NUM_WORKERS=6
export PORT_INIT=3070


cleanup() {
    echo "Caught Interrupt signal. Cleaning up..."
    # Kill all child processes of this script
    pkill -P $$
}

trap cleanup SIGINT


export gpu="python3 /shared/cathychen/gpu_scheduler/reserve.py"


# Start captioner_server.py on different ports
captioner_pids=()
for (( i=0; i<NUM_WORKERS; i++ )); do
    echo "Starting captioner_server.py on port $((PORT_INIT+i))"
    $gpu "python captioner_server.py --port $((PORT_INIT+i))" &
    captioner_pids+=($!)
done


# Wait for the servers to start 
echo "Waiting for captioner_server.py to start..."
sleep 60

# Start prepare_caps_sub.py with different parameters and store their PIDs
prepare_pids=()
for (( i=0; i<NUM_WORKERS; i++ )); do
    echo "Starting prepare_caps_sub.py with idx $i" 
    python prepare_caps_sub.py --port $((PORT_INIT+i)) --idx $i --total $NUM_WORKERS --images_path $IMAGES_PATH --output_path $OUTPUT_PATH --only-last-two &
    prepare_pids+=($!) 
done

# Wait for all prepare_caps_sub.py jobs to finish
for pid in ${prepare_pids[@]}; do
    wait $pid
done

# Stop all captioner_server.py processes
for pid in ${captioner_pids[@]}; do
    kill $pid
done
