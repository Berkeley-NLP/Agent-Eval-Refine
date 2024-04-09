from tqdm import tqdm
import json
from human_id import generate_id
import os
import argparse
import multiprocessing as mp

from agent_eval.clients import LM_Client, GPT4V_Client
from agent_eval.domains.unified import UniTrajectoryDataset
from agent_eval.eval.evaluator import Evaluator
from agent_eval.eval.metrics import get_metrics_from_result_json
from termcolor import cprint
import random

PROJECT_ROOT = os.environ.get(
    "PROJECT_ROOT", "/home/<user>/code/<removed>_GUI/agent_eval"
)


def process_sample(
    idx: str,
    traj_info: dict,
    # evaluator: Evaluator,
    log_save_path,
    model: str,
    eval_version: str,
) -> list[dict]:
    # print(idx, model)
    # try:
    if True:
        oai_key = "<removed>"
        clients = {
            "gpt-3.5": LM_Client(api_key=oai_key, model_name="gpt-3.5"),
            "gpt-4": LM_Client(api_key=oai_key, model_name="gpt-4"),
            "mixtral": LM_Client(api_key="<removed>", model_name="mixtral"),
            "gpt-4v": GPT4V_Client(api_key=oai_key),
        }
        evaluator = Evaluator(clients, log_save_path=log_save_path + "/trajs")
        out, _ = evaluator(traj_info, model, eval_version)
        eval_result = None
        if out["status"] == "success" or out["status"] == "Success":
            eval_result = True
        else:
            eval_result = False
        return [
            {
                "idx": idx,
                "gt": traj_info["eval"],
                "rm": eval_result,
                "uid": traj_info["traj_name"],
            }
        ]
    # except Exception as e:
    #     print(f"Error on {idx}, {e}")
    #     print(traceback.format_exc())
    #     return []


def main(args):
    main_config = {
        "caption_data": "ocr-sft-qwenvl-v2",
        # "model": args.model,
        # "model": "gpt-4v",
        # "model": "gpt-3.5",
        # "model": "mixtral",
        "model": "gpt-4",
        # "eval_version": args.prompt,
        # "eval_version": "android-gpt4v",
        "eval_version": "android",
    }
    data_config = {
        # "dataset_path": "/home/<user>/data/GUI_Proj/unified_datasets/webarena-gpt4cot-release2/",
        # "dataset_path": "/home/<user>/data/GUI_Proj/unified_datasets/ios80-cogagent-v0/",
        # "dataset_path": "/home/<user>/data/GUI_Proj/unified_datasets/android-cogagent-v0/",
        # "dataset_path": "/home/<user>/data/GUI_Proj/unified_datasets/android-cogagent-v0/",
        # "dataset_path": "/home/<user>/data/android_offline/output_autoui_base_filteredbc_test/",
        "dataset_path": "/home/<user>/data/GUI_Proj/android_result/output_autoui_base/",
        # "dataset_path": "/home/<user>/data/GUI_Proj/android_result/output_autoui_large/",
        # "dataset_path": "/home/<user>/data/GUI_Proj/android_result/output_cogagent/",
        # "dataset_path": "/home/<user>/data/GUI_Proj/android_result/android-gt/",
        "eval_log_names": ["filered_v0"],
    }

    log_save_path = os.path.join(PROJECT_ROOT, "outputs", generate_id(word_count=3))
    assert not os.path.exists(log_save_path)
    os.makedirs(log_save_path)
    os.makedirs(log_save_path + "/trajs")
    cprint(f"Saving logs to {log_save_path}", "cyan")

    dev_dataset = UniTrajectoryDataset(
        **data_config,
        captioner_name=main_config["caption_data"],
        load_image=True if main_config["model"] == "gpt-4v" else False,
    )
    samples_to_eval = dev_dataset.get_idx_list_with_annotations()

    # if "webarena" in data_config["dataset_path"]:
    #     samples_to_eval = [dev_dataset.uid_to_idx(uid) for uid in webarena_dev_uid_list]
    # samples_to_eval = [dev_dataset.uid_to_idx(uid) for uid in webarena_val_uid_list]

    # random.seed(20)
    # samples_to_eval = random.sample(samples_to_eval, 50)

    pool = mp.Pool(args.num_proc)
    jobs = [
        pool.apply_async(
            process_sample,
            args=(
                idx,
                dev_dataset[idx],
                log_save_path,
                main_config["model"],
                main_config["eval_version"],
            ),
        )
        for idx in samples_to_eval
    ]
    pool.close()

    def get_gt_label(result):
        for user_uid, ann in result["gt"].items():
            return ann["annotation"] == "Success"

    results = {}
    for job in tqdm(jobs):
        for res in job.get():
            results[res["uid"]] = {"gt": get_gt_label(res), "rm": res["rm"]}

    with open(log_save_path + "/rm_results.json", "w") as f:
        json.dump(results, f, indent=4)

    metrics, _ = get_metrics_from_result_json(log_save_path + "/rm_results.json")
    metrics["config"] = {
        "model": main_config["model"],
        "eval_version": main_config["eval_version"],
        "caption_data": main_config["caption_data"],
        "samples_to_eval": samples_to_eval,
        "dataset_path": data_config["dataset_path"],
    }
    with open(log_save_path + "/stats.json", "w") as f:
        json.dump(metrics, f, indent=4)
    print(metrics)


if __name__ == "__main__":
    random.seed(42)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        type=str,
        choices=["gpt-3.5", "gpt-4", "mixtral", "gpt-4v"],
        default="gpt-3.5",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        choices=[
            "naive-last-frame",
            "naive-last-frame-v2",
            "naive-last-frame-4v",
            "naive-multi-frame",
            "naive-multi-frame-v2",
            "simplify-last-frame",
            "simplify-last-frame-v2",
            "simplify-last-3-frame",
            "simplify-last-3-frame-v2",
            "final-v2",
            "final-v3",
            "final-v3-gpt4v",
        ],
        default="final-v3",
    )
    parser.add_argument("--num_proc", type=int, default=10)
    args = parser.parse_args()

    main(args)
