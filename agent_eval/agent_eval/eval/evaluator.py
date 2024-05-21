import json
import os
from typing import Any, List, Tuple

from termcolor import cprint

from agent_eval.eval.prompts import *


class Evaluator:
    def __init__(self, lm_clients, log_save_path=None):
        self.lm_clients = lm_clients
        self.log_save_path = log_save_path

    def __call__(self, info, client="gpt-3.5", version="naive"):
        assert (
            client in self.lm_clients
        ), f"Client {client} not found in {self.lm_clients.keys()}"
        if version == "final-v3":
            eval_info, eval_str, prompt = self.final_eval_v3(info, client)
        elif version == "final-v3-gpt4v":
            eval_info, eval_str, prompt = self.final_eval_v3_gpt4v(info, client)
        elif version == "android":
            eval_info, eval_str, prompt = self.eval_android(info, client)
        elif version == "android-gpt4v":
            eval_info, eval_str, prompt = self.eval_android_gpt4v(info, client)
        elif version == "naive-last-frame-4v":
            eval_info, eval_str, prompt = self.naive_last_frame_eval_4v(info, client)
        else:
            raise NotImplementedError(f"Version {version} not implemented")

        if self.log_save_path:
            with open(self.log_save_path + "/outputs.jsons", "a") as f:
                f.write(
                    json.dumps(
                        {
                            "id": info["traj_name"],
                            "eval_info": eval_info,
                        }
                    )
                    + "\n"
                )
            with open(f"{self.log_save_path}/{info['traj_name']}.md", "w") as md_file:
                md_file.write(f"## Intent\n\n{info['intent']}\n\n")
                md_file.write(f"## RM\n\n{eval_str}\n\n")
                md_file.write(f"## Final Response {info['response']}\n\n")
                if "captions" in info and info['captions'] is not None:
                    md_file.write("## Captions\n\n")
                    for idx, cap in enumerate(info["captions"]):
                        md_file.write(f"===============")
                        md_file.write(f"{cap}\n")
                md_file.write("\n## Images\n\n")
                for idx, img in enumerate(info["image_paths"]):
                    rel_img_path = os.path.relpath(img, self.log_save_path)
                    md_file.write(f"![Image {idx+1}]({rel_img_path})\n")

                if "config" in info:
                    md_file.write("## Config\n\n")
                    cofig_str = json.dumps(info["config"], indent=4)
                    md_file.write(f"```json\n{cofig_str}\n```\n")
                if prompt:
                    md_file.write("## Main Prompt\n\n")
                    md_file.write(f"```md\n{prompt}\n```\n")
        return eval_info, prompt

    def naive_last_frame_eval_4v(self, info, client):
        assert client == "gpt-4v"
        prompt, sys_msg = build_naive_last_frame_4v_eval_prompt(
            info["intent"],
            info["response"] if info["response"] else "None",
        )
        img = info["images"][-1]
        lm_client = self.lm_clients[client]
        msg_str, _ = lm_client.one_step_chat(
            prompt, img, system_msg=sys_msg, json_mode=False
        )
        msg_dict = json.loads(msg_str)
        return msg_dict, msg_str, prompt

    def final_eval_v3(self, info, client):
        response = info["response"] if info["response"] else "None"
        lm_client = self.lm_clients[client]
        action_history = ""
        for idx, act in enumerate(info["actions"]):
            action_history += f"{idx+1}: {act}\n"
        prompt, sys_msg = build_final_eval_v3_final_prompt(
            info["captions"][-1], info["intent"], response, action_history
        )
        # lm_client = self.lm_clients["gpt-4"]
        msg_str, _ = lm_client.one_step_chat(prompt, system_msg=sys_msg)
        msg_dict = {
            "thoughts": extract_content(msg_str, "Thoughts:"),
            "status": extract_content(msg_str, "Status:").replace('"', ""),
        }
        return msg_dict, msg_str, prompt

    def final_eval_v3_gpt4v(self, info, client):
        assert client == "gpt-4v"
        action_history = ""
        for idx, act in enumerate(info["actions"]):
            action_history += f"{idx+1}: {act}\n"
        prompt, sys_msg = build_final_eval_v3_final_prompt_gpt4v(
            info["intent"], info["response"], action_history
        )
        img = info["images"][-1]
        
        lm_client = self.lm_clients[client]
        msg_str, _ = lm_client.one_step_chat(
            prompt, img, system_msg=sys_msg, json_mode=False
        )
        del info["images"]
        # msg_dict = json.loads(msg_str)
        msg_dict = {
            "thoughts": extract_content(msg_str, "Thoughts:"),
            "status": extract_content(msg_str, "Status:").replace('"', ""),
        }
        return msg_dict, msg_str, prompt

    def eval_android_gpt4v(self, info, client):
        assert client == "gpt-4v"
        action_history = ""
        for idx, act in enumerate(info["actions"]):
            action_history += f"{idx+1}: {act}\n"
        prompt, sys_msg = build_android_prompt_gpt4v(
            info["intent"], info["response"], action_history
        )
        img = {"image":info["images"][-1], "detail": "high"}
        # if len(info["images"]) >= 2:
        #     sec_img = {"image":info["images"][-2], "detail": "high"}
        #     image_input = [sec_img, img]
        # else:
        #     image_input = [img]

        image_input = [img]
        lm_client = self.lm_clients[client]
        # msg_str, _ = lm_client.one_step_chat(
        #     prompt, img, system_msg=sys_msg, json_mode=False
        # )
        msg_str, _ = lm_client.one_step_multi_image_chat(
            prompt, image_input, system_msg=sys_msg, json_mode=False
        )
        # msg_dict = json.loads(msg_str)
        msg_dict = {
            "thoughts": extract_content(msg_str, "Thoughts:"),
            "status": extract_content(msg_str, "Status:").replace('"', ""),
        }
        return msg_dict, msg_str, prompt

    def eval_android(self, info, client):
        response = info["response"] if info["response"] else "None"
        lm_client = self.lm_clients[client]
        action_history = ""
        for idx, act in enumerate(info["actions"]):
            action_history += f"{idx+1}: {act}\n"
        prompt, sys_msg = build_android_prompt(
            info["captions"][-1], info['captions'][-2] if len(info['captions']) > 1 else None,
            info["intent"], response, action_history
        )
        msg_str, _ = lm_client.one_step_chat(prompt, system_msg=sys_msg)
        msg_dict = {
            "thoughts": extract_content(msg_str, "Thoughts:"),
            "status": extract_content(msg_str, "Status:").replace('"', ""),
        }
        return msg_dict, msg_str, prompt