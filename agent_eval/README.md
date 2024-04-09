## Setup
First install the `agent_eval` package
```
cd agent_eval
pip install -e .
```

If you want to do inference with the captioner model, you need to additionally revert the `transformers` package to an old version 

```
pip install transformers==4.32.0
```
## Evaluate Agent Trajectories

## Captioner

- `./agent_eval/captioner/annotate_screenshots.py` include code to annotate the screenshots with GPT-4V
- `./agent_eval/captioner/captioner_server.py` include code to run the captioner server with [pre-trained weights](https://huggingface.co/Agent-Eval-Refine/Captioner).

## Start Captioner Server
```
conda activate qwenvl
gpu "python -m agent_eval.captioner.captioner_server --port 2333 --share"
```

## Run WebArena Eval
To modify the prompting pipeline, check out `agent_eval/eval/evaluator.py` and `agent_eval/eval/prompts.py`

To run eval
```python
python scripts/run_eval_uni.py --model mixtral --prompt final-v3
```

The statistics will be print out once the eval is finished and the logs will be stored at `outputs/Unique-ID` folder.

## How to Prepare iOS Dataset
1. `/home/<user>/code/<removed>_GUI/agent_eval/agent_eval/domains/unify_ios_data.ipynb` edit the source path in this notebook and run it to generate `trajectory_log.json` file.
2. move that json to your original dataset path
3. Create another two folders named `evals` and `captions`
4. Run the annotation app `/home/<user>/code/<removed>_GUI/agent_eval/agent_eval/eval/annotate_app.py`
for example
```
python annotate_app.py --dataset /home/<user>/data/GUI_Proj/gpt4_deterministic_jan28/ --log_name v0
```
## Inspect Datasets
```
conda activate GPML 

python -m agent_eval.eval.annotate_app --dataset /home/<user>/data/GUI_Proj/unified_datasets/android-gt/ --log_name v0

python -m agent_eval.eval.annotate_app --dataset /home/<user>/data/GUI_Proj/web_reflexion/gt-baseline-v0/ --log_name gt
python -m agent_eval.eval.annotate_app --dataset /home/<user>/data/GUI_Proj/web_reflexion/gae-nl-v0/ --log_name gt

python -m agent_eval.eval.annotate_app --dataset /home/<user>/data/GUI_Proj/unified_datasets/android-gt/ --log_name v0
```