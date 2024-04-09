# %%
import agent_eval
from agent_eval.domains.webarena import extract_trajectory_info, extract_eval_results
import json
import os

# %%
# raw_dataset_path = "/home/<user>/code/WebArena/webarena_traj/102023_release_v2/919_gpt4_8k_cot"
# output_dataset_path = "/home/<user>/data/GUI_Proj/unified_datasets/webarena-gpt4cot-release2"

# raw_dataset_path ="/home/<user>/code/WebArena/webarena_traj/102023_release_v2/919_gpt35_16k_cot"
# output_dataset_path = "/home/<user>/data/GUI_Proj/unified_datasets/webarena-gpt35cot-release2"

raw_dataset_path = "/home/<user>/code/WebArena/webarena_traj/gpt4_v1"
output_dataset_path = (
    "/home/<user>/data/GUI_Proj/unified_datasets/webarena-gpt4cot-release1"
)


assert not os.path.exists(output_dataset_path)
os.makedirs(output_dataset_path)
os.makedirs(os.path.join(output_dataset_path, "images"))
os.makedirs(os.path.join(output_dataset_path, "evals"))
os.makedirs(os.path.join(output_dataset_path, "captions"))

# %% [markdown]
# ### Record WebArena's Eval Results

# %%
log_str = open(os.path.join(raw_dataset_path, "merged_log.txt")).read()
eval_results = extract_eval_results(log_str)
formated_eval_results = []
for uid, eval_result in eval_results.items():
    formated_eval_results.append(
        {
            "dataset_path": output_dataset_path.split("/")[-1],
            "task_idx": uid,
            "task_uid": uid,
            "user_uid": "WebArena",
            "annotation": "Success" if eval_result else "Failure",
            "comment": "",
        }
    )
with open(os.path.join(output_dataset_path, "evals", "gt.jsonl"), "w") as file:
    for item in formated_eval_results:
        # Convert each dictionary to a JSON string and write it to a file
        json_string = json.dumps(item)
        file.write(json_string + "\n")


# %% [markdown]
# ### Get the Trajectory Log and Images

# %%
all_files = os.listdir(raw_dataset_path)
trajs = [f for f in all_files if f.endswith(".html")]

# %%
html_content_str = open(os.path.join(raw_dataset_path, trajs[0])).read()

# %%
extract_trajectory_info(html_content_str)

# %%
trajs[0]

# %%
html_content_str = open(os.path.join(raw_dataset_path, "render_40.html")).read()
info = extract_trajectory_info(html_content_str)

# %%
info

# %%
from tqdm import tqdm
import re

traj_log = []
for traj_name in tqdm(trajs):
    html_content_str = open(os.path.join(raw_dataset_path, traj_name)).read()
    traj_id = traj_name.replace(".html", "").replace("render_", "")
    info = extract_trajectory_info(html_content_str)
    # save the image
    images = info["images"]

    if len(images) != len(info["actions"]):
        print(
            f"{traj_id} has {len(images)} images but {len(info['actions'])} actions | skip"
        )
        continue
    for img_idx, img in enumerate(images):
        img_name = f"{traj_id}_{img_idx}.png"
        img.save(os.path.join(output_dataset_path, "images", img_name))
    match = re.search(r"<pre>(.*?)</pre>", html_content_str, re.DOTALL)
    config = match.group(1) if match else None
    this_log = {
        "uid": traj_id,
        "intent": info["intent"],
        "response": info["response"],  # TODO
        "other": {"config": config},
        "steps": [],
    }
    for step_idx, (img, action) in enumerate(zip(images, info["actions"])):
        img_name = f"{traj_id}_{step_idx}.png"
        this_log["steps"].append({"img": img_name, "other": {"raw_action": action}})
    traj_log.append(this_log)
with open(os.path.join(output_dataset_path, "trajectory_log.json"), "w") as file:
    json.dump(traj_log, file, indent=2)
