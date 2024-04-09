import os
from typing import Any
from gradio_client import Client
from browser_env import Trajectory
import numpy as np
import tempfile
from PIL import Image
from typing import Union, Literal
import time
from agent_eval.clients import LM_Client, GPT4V_Client
from agent_eval.eval.evaluator import Evaluator
import multiprocessing as mp
import re
import random

OAI_KEY = os.getenv("OPENAI_API_KEY")

CAPTION_CLIENT_URLS = os.getenv("CAPTION_CLIENT_URLS")
CAPTION_CLIENT_URLS = CAPTION_CLIENT_URLS.split(" ") if CAPTION_CLIENT_URLS else []


class GUIAgentEvaluator:
    def __init__(
        self,
        result_path: str,
        model_type: str = "mixtral",
        prompt_version: str = "final-v2",
    ):
        self.model_type = model_type
        self.prompt_version = prompt_version
        self.client_urls = CAPTION_CLIENT_URLS
        self.num_caption_clients = len(CAPTION_CLIENT_URLS)
        self.caption_clients = [Client(url) for url in CAPTION_CLIENT_URLS]
        self.lm_clients = {
            "gpt-3.5": LM_Client(api_key=OAI_KEY, model_name="gpt-3.5"),
            "gpt-4": LM_Client(api_key=OAI_KEY, model_name="gpt-4"),
            "mixtral": LM_Client(api_key="<removed>", model_name="mixtral"),
            "gpt-4v": GPT4V_Client(api_key=OAI_KEY),
        }
        self.evaluator = Evaluator(self.lm_clients, log_save_path=result_path)

    def caption(self, image: Union[str, Image.Image, np.array], idx: int = -1) -> str:
        start_t = time.time()
        # print(f"captioning image {idx}")
        if idx < 0:
            client = random.choice(self.caption_clients)
        else:
            client = self.caption_clients[idx % self.num_caption_clients]
        if isinstance(image, str):
            caption = client.predict(image, api_name="/predict")
        else:
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image)
            with tempfile.NamedTemporaryFile(suffix=".png") as f:
                print(f.name)
                image.save(f.name)
                caption = client.predict(f.name, api_name="/predict")
        print(f"captioning took {time.time() - start_t}")
        # print(caption)
        return caption

    def __call__(self, records: dict) -> tuple[float, str]:
        # (s, a, s, a, ...)
        # if len(records["steps"]) == 1:
        #     captions = [self.caption(records["steps"][-1]["img"], idx=0)]
        # else:
        #     pool = mp.Pool(2)
        #     jobs = [
        #         pool.apply_async(self.caption, args=(step["img"], idx))
        #         for idx, step in enumerate(records["steps"][-2:])
        #     ]
        #     pool.close()
        #     captions = [job.get() for job in jobs]

        # Note: we only caption the last two observations
        if "captions" not in records and self.model_type != "gpt-4v":
            captions = [self.caption(s["img"]) for s in records["steps"][-2:]]
            records["captions"] = captions
        records["actions"] = self._get_actions(records)
        records["traj_name"] = f"eval_{records['uid']}_{records['trail_idx']}"
        records["image_paths"] = [step["img"] for step in records["steps"]]
        if self.model_type == "gpt-4v":
            records["images"] = []
            for img_path in records["image_paths"]:
                with Image.open(img_path) as img:
                    records["images"].append(np.array(img))

        out, _ = self.evaluator(records, self.model_type, self.prompt_version)
        print(out)
        if "success" in out["status"]:
            # return 0, "FAILED"
            return 1, out["thoughts"]
        else:
            # return 1, "PASSED"
            return 0, out["thoughts"]

    def _get_actions(self, dp):
        actions = []
        for step in dp["steps"]:
            action = None
            try:
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
            except Exception as e:
                print("Error in extracting acrtion", e, step)
            actions.append(action)
        return actions
