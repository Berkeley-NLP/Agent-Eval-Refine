#!/bin/bash

### Environmental variables
# Server URL for the WebArena websites
SERVER="localhost"

# OpenAI API key
OPENAI_API_KEY="<removed>"

# Captioner client URLs separated by space
CAPTION_CLIENT_URLS=""

# Conda environment name
CONDA_ENV_NAME="webarena"

# The command to export all the environmental variables
ENV_VARIABLES="export SHOPPING='http://${SERVER}:7770';export SHOPPING_ADMIN='http://${SERVER}:7780/admin';export REDDIT='http://${SERVER}:9999';export GITLAB='http://${SERVER}:8023';export MAP='http://miniserver1875.asuscomm.com:3000';export WIKIPEDIA='http://${SERVER}:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing';export HOMEPAGE='http://${SERVER}:4399';export OPENAI_API_KEY=${OPENAI_API_KEY};export CAPTION_CLIENT_URLS=${CAPTION_CLIENT_URLS}"


### Experimental configurations

# The reflexion agent model
model="gpt-4-1106-preview" 

# The prompt template
instruction_path="agent/prompts/jsons/p_cot_id_actree_2s_reflexion.json"

# Randomly sampled 100 test cases from the original WebArena test set
test_file="config_files/test_random_sampled_100.json" 

# The number of trails attempts
max_num_attempts=4 # 1 + 3 retries

# Use our model-based evaluator
reflexion_evaluator="model"

# Directory for the baseline experiment. If a trajectory for task x, trail y is available, we will reuse that trajectory without running the agent again. The agent with the oracle evaluator should be run first to produce this baseline results.  
baseline_dir="outputs/gpt4-oracle-r${max_num_attempts}-100tasks"

# Set up the evaluator model. Options: gpt-4v, gpt-4, mixtral
eval_lm_model="gpt-4v"

if [ ${eval_lm_model}="gpt-4v" ]
then
    # use the GPT-4V prompt 
    eval_prompt_version="final-v3-gpt4v"
    result_dir="outputs/gpt4-gpt4v-r${max_num_attempts}-100tasks"
else
    # use the text-only prompt for GPT-4 and mixtral
    eval_prompt_version="final-v3"
    result_dir="outputs/gpt4-cap_${eval_lm_model}-r${max_num_attempts}-100tasks"
fi


### Code to run the experiments

# get the number of tmux panes
num_panes=$(tmux list-panes | wc -l)

# calculate how many panes need to be created
let "panes_to_create = 6 - num_panes"

# array of tmux commands to create each pane
tmux_commands=(
    'tmux split-window -h'
    'tmux split-window -v'
    'tmux select-pane -t 0; tmux split-window -v'
    'tmux split-window -v'
    'tmux select-pane -t 3; tmux split-window -v'
)

# create panes up to 5
for ((i=0; i<$panes_to_create; i++)); do
    eval ${tmux_commands[$i]}
done

#!/bin/bash

# Function to run a job
run_job() {
    tmux select-pane -t $1
    tmux send-keys "conda activate ${CONDA_ENV_NAME}; ${ENV_VARIABLES}; until python run_reflexion.py --agent_type reflexion --test_start_idx $2 --test_end_idx $3 --test_file ${test_file} --model ${model} --max_num_attempts ${max_num_attempts} --instruction_path ${instruction_path} --result_dir ${result_dir} --baseline_dir ${baseline_dir} --reflexion_evaluator ${reflexion_evaluator} --eval_prompt_version ${eval_prompt_version} --eval_lm_model ${eval_lm_model}; do echo 'crashed' >&2; sleep 1; done" C-m
    sleep 3
}

TOLERANCE=2
run_batch() {
    args=("$@") # save all arguments in an array
    num_jobs=${#args[@]} # get number of arguments

    for ((i=1; i<$num_jobs; i++)); do
        run_job $i ${args[i-1]} ${args[i]}
    done

    # Wait for all jobs to finish
    while tmux list-panes -F "#{pane_pid} #{pane_current_command}" | grep -q python; do
        sleep 100  # wait for 10 seconds before checking again
    done

    # # Run checker
    # while ! python scripts/check_error_runs.py ${result_dir} --delete_errors --tolerance ${TOLERANCE}; do
    #     echo "Check failed, rerunning jobs..."
    #     for ((i=1; i<$num_jobs; i++)); do
    #         run_job $i ${args[i-1]} ${args[i]}
    #     done

    #     # Wait for all jobs to finish
    #     while tmux list-panes -F "#{pane_pid} #{pane_current_command}" | grep -q python; do
    #         sleep 100  # wait for 10 seconds before checking again
    #     done
    # done

}

# run the 5 experiments in parallel
# run_batch 0 20 40 60 80 100
run_batch 0 1 2 3 4 5

## reset env
# cd ../webarena_ori/dockers
# sh ../../webarena/reset_docker.sh
# cd ../../webarena
# echo "Dockers Reset!"