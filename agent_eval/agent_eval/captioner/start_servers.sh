#!/bin/bash
# Set the variables


export IMAGES_PATH=/home/<user>/data/GUI_Proj/unified_datasets/android-cogagent-v0/images
export OUTPUT_PATH=/home/<user>/data/GUI_Proj/unified_datasets/android-cogagent-v0/new_caption_output.json
export NUM_WORKERS=1
export PORT_INIT=3050

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
    $gpu "python captioner_server.py --port $((PORT_INIT+i)) --share" &
    captioner_pids+=($!)
done