#!/bin/bash
OUTPUT_DIR="output_autoui_large"
mkdir -p "$OUTPUT_DIR"
FILE="assets/instructions.txt"
TOTAL_LINES=$(wc -l < "$FILE") # Get the total number of lines/tasks
CURRENT_LINE=0

if [ ! -f "$FILE" ]; then
    echo "File $FILE does not exist."
    exit 1
fi

echo "Starting tasks..."

while IFS= read -r line
do
    CURRENT_LINE=$((CURRENT_LINE+1))

    # Print the progress
    echo -ne "Progress: [$CURRENT_LINE/$TOTAL_LINES]\r"

    appium --relaxed-security 1> $OUTPUT_DIR/appium_output.txt &
    APP_PID=$!
    sleep 10

    timeout 25m python main.py --task "$line" --output_dir "$OUTPUT_DIR" --agent "autoui-large"

    kill $APP_PID
    sleep 10
done < "$FILE"

echo "All tasks completed."
