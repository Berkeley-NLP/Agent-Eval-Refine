from agent_eval.eval.annotator import Annotator
from agent_eval.domains.unified import UniTrajectoryDataset
from agent_eval.clients import LM_Client, GPT4V_Client
import multiprocessing as mp
from tqdm import tqdm
import json


def process_sample(
    traj_info: dict,
    model: str,
):
    try:
        print("processing: ", traj_info["traj_name"])
        oai_key = "<removed>"
        clients = {
            "gpt-3.5": LM_Client(api_key=oai_key, model_name="gpt-3.5"),
            "gpt-4": LM_Client(api_key=oai_key, model_name="gpt-4"),
            "mixtral": LM_Client(api_key="<removed>", model_name="mixtral"),
            "gpt-4v": GPT4V_Client(api_key=oai_key),
        }
        annotator = Annotator(clients)
        out = annotator(traj_info, model, "v1")
        return {
            "uid": traj_info["traj_name"],
            "per_step_eval": out,
        }

    except Exception as e:
        print(f"Error on {traj_info['traj_name']}, {e}")
        return None


def main():
    data_config = {
        "dataset_path": "/home/<user>/data/GUI_Proj/unified_datasets/ios80-cogagent-v0/",
        "eval_log_names": ["v0"],
    }
    dev_dataset = UniTrajectoryDataset(
        **data_config, captioner_name="ocr-sft-qwenvl-v2", load_image=False
    )
    pool = mp.Pool(20)
    jobs = [
        pool.apply_async(
            process_sample,
            args=(dev_dataset[idx], "mixtral"),
        )
        for idx in range(len(dev_dataset))
        # for idx in range(20)
    ]
    pool.close()

    results = {}
    for job in tqdm(jobs):
        res = job.get()
        if res is None:
            continue
        results[res["uid"]] = res["per_step_eval"]
    with open(
        "/home/<user>/data/android_offline/output_autoui_base_300/traj_annotations-mixtral.json",
        "w",
    ) as f:
        json.dump(results, f)


if __name__ == "__main__":
    main()
