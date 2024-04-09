from PIL import Image
import os
import json
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from termcolor import cprint
import re
import numpy as np

class UniTrajectoryDataset:
    def __init__(
        self,
        dataset_path: str,
        eval_log_names: List[str],
        captioner_name: str = "ocr-sft-qwenvl-v1",
        load_image=True,
    ) -> None:
        assert dataset_path[-1] == "/", "dataset_path must end with a /"
        self.dataset_path = dataset_path
        self.data_log = json.load(open(dataset_path + "trajectory_log.json", "r"))
        cprint(f"Using dataset: {dataset_path}", "green")
        if os.path.exists(dataset_path + "captions/" + captioner_name + ".json"):
            self.captions = json.load(
                open(dataset_path + "captions/" + captioner_name + ".json", "r")
            )
        else:
            self.captions = None
        cprint(f"Using eval logs from: {eval_log_names}", "green")
        self.evals = defaultdict(lambda: defaultdict())
        for eval_log_name in eval_log_names:
            eval_log_path = dataset_path + "evals/" + eval_log_name + ".jsonl"
            with open(eval_log_path, "r") as f:
                for line in f:
                    ann = json.loads(line)
                    if ann["task_uid"] != "" and ann["task_idx"] != -1:
                        self.evals[ann["task_uid"]][ann["user_uid"]] = ann
        self.uid_to_idx_map = {dp["uid"]: idx for idx, dp in enumerate(self.data_log)}
        self.idx_to_uid_map = {idx: dp["uid"] for idx, dp in enumerate(self.data_log)}
        self.load_image = load_image

    def uid_to_idx(self, uid):
        return self.uid_to_idx_map[uid]

    def idx_to_uid(self, idx):
        return self.idx_to_uid_map[idx]

    def get_idx_list_with_annotations(self):
        return [self.uid_to_idx(uid) for uid in self.evals.keys()]

    def __len__(self):
        return len(self.data_log)

    def __getitem__(self, idx):
        dp = self.data_log[idx]
        imgs = None
        if self.load_image:
            imgs = []
            for step in dp["steps"]:
                img = Image.open(self.dataset_path + f"images/{step['img']}")
                img.load()
                imgs.append(img)
        info = {
            "intent": dp["intent"],
            "images": imgs,
            "image_paths": [
                self.dataset_path + f"images/{step['img']}" for step in dp["steps"]
            ],
            "response": dp["response"],
            "captions": [self.captions[f"{step['img'][:-4]}"] for step in dp["steps"]]
            if self.captions
            else None,
            "traj_name": dp["uid"],
            "eval": self.evals[dp["uid"]] if dp["uid"] in self.evals else None,
            "actions": self._get_actions(dp),
        }
        # assert len(info['captions']) == len(info['images']), f"traj {idx} has {len(info['captions'])} captions and {len(info['images'])} images"
        return info

    def _get_actions(self, dp):
        actions = []
        for step in dp["steps"]:
            action = None
            try:
                if "web" in self.dataset_path:
                    raw_action = step["other"]["raw_action"]
                    splits = raw_action.split(" ")
                    if not splits:
                        action = raw_action.replace("_", " ")
                    elif splits[0] == "click":
                        element_str = " ".join(splits[6:])
                        action = f"click at [{element_str}]"
                    elif splits[0] in ["scroll", "stop"]:
                        action = raw_action
                    elif splits[0] == "type":
                        matches = re.findall(r"\[(.*?)\]", raw_action)
                        typed = matches[1].strip()
                        last_bracket_pos = raw_action.rfind("]")
                        element_str = raw_action[last_bracket_pos + 1 :].strip()
                        action = f"type [{typed}] at [{element_str}]"
                    else:
                        action = raw_action
                elif "ios" in self.dataset_path:
                    action = step["other"]["translated_action"]
                    if "tap" in action:
                        action = "tap"
                elif "android" in self.dataset_path:
                    action = step["other"]["action"]
                    if "DualPoint" in action:
                        # Regex to find all numbers, including decimals
                        coordinates = re.findall(r"(\d+\.\d+)", action)

                        # Convert found strings to float and assign to variables
                        # Since the points are the same, we technically only need to parse two numbers, but for completeness:
                        x1, y1, x2, y2 = map(float, coordinates)

                        # Calculate the distance with numpy
                        distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

                        # Check if the distance is larger than 0.05
                        is_distance_larger_than_0_05 = distance > 0.05
                        if is_distance_larger_than_0_05:
                            action = "swipe on screen"
                        else:
                            action = "tap"
            except Exception as e:
                print("Error in extracting acrtion", e, step)
            actions.append(action)
        return actions
