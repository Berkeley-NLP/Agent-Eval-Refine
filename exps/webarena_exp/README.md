# WebArena: A Realistic Web Environment for Building Autonomous Agents

## Install

```bash
# Python 3.10+
conda create -n webarena python=3.10; conda activate webarena
pip install -r requirements.txt
playwright install
pip install -e .

# optional, dev only
pip install -e ".[dev]"
mypy --install-types --non-interactive browser_env agents evaluation_harness
pip install pre-commit
pre-commit install
```

## Setup WebArena Environment

1. Launch the website servers following the instructions on [this page](environment_docker/README.md).

2. Modify the server address in `scripts/prepare_webarena.sh` and run the script to prepare the webarena tasks.

Note: please refer to the original [webarena repo](https://github.com/web-arena-x/webarena) for more detailed instructions.

```bash
scripts/prepare_webarena.sh
```

## End-to-End Evaluation
We provide 4 scripts to run the experiments:

```
# Evaluate on a randomly sampled subset of 100 tasks
parallel_run_oracle.sh   # Run Reflexion with the oracle evaluator
parallel_run_gae.sh      # Run Reflexion with our evaluator

# Evaluate on the entire WebArena test set (812 tasks)
parallel_run_oracle_all.sh   # Run Reflexion with the oracle evaluator
parallel_run_gae_all.sh      # Run Reflexion with our evaluator
```

Steps to reproduce the paper results:

1. Start one or multiple caption clients following the instructions [here](../../README.md). 

2. Add captioner client urls and the OpenAI API key into the script. You may also need to modify `SERVER` and `CONDA_ENV_NAME` according to your setup. 

3. Open a tmux session: `tmux`

4. Run the script in the tmux session. The script will automatically spawn 5 tmux windows to run the tasks in parallel. First run with the oracle evaluator to get the baseline trajectories. 

```bash
./parallel_run_oracle_all.sh
```

5. Sometimes part of the tasks may be failed to finish due to various issues including api errors, exceptions from the webarena environment etc. This can be addressed by repeating running the scripts several times until all the tasks are successfully completed.

6. Run with our model-based evaluator. You can modify the `eval_lm_model` in the `parallel_run_oracle_all.sh` script to select different evaluation models. 

```bash
./parallel_run_gae_all.sh
```

Note: In these experiments we reuse the trajectories from the oracle evaluator to save the cost. If a trajectory for task x, trail y exists in the baseline experiment, we will reuse the trajectory without running the agent again. This can be achieved by setting the `baseline_dir` to the `result_dir` of step 4. 

7. Repeat until are the tasks are completed without errors, similar to step 5. 

Note: There is no good way to reset the website state in WebArena (see [this issue](https://github.com/web-arena-x/webarena/issues/88)). We recommend resetting the dockers between different runs of the experiments. We provide a utility script `reset_docker.sh` for this purpose. 

## Result Analysis

Run the notebook `result_analysis.ipynb` under `scripts`. 
