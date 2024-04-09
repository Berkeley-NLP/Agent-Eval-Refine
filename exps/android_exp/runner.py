from env import AndroidEnv
from client import AbstractAgent
import time

import time
import uuid
import os
import json
from termcolor import colored, cprint

def create_human_friendly_uid():
    current_time_str = time.strftime("%m%d_%H%M%S")
    # Generate a random UUID
    random_uuid = str(uuid.uuid4()).split("-")[0]
    # Create a unique string combining the time and UUID
    unique_string = f"{current_time_str}-{random_uuid}"
    return unique_string



class Runner:
    def __init__(self, task_prompt: str, env: AndroidEnv, agent: AbstractAgent, log_path: str, verbose: bool = True):
        self.task_prompt = task_prompt
        self.env = env
        self.agent = agent
        self.log_path = log_path
        self.image_path = os.path.join(self.log_path, "images")
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)
        if not os.path.exists(self.image_path):
            os.makedirs(self.image_path)
        self.uid = create_human_friendly_uid()
        self.current_step = 0
        self.log = []
        self.verbose = verbose
    
    def _save_img(self, obs):
        if obs:
            img_path = os.path.join(self.image_path, f"{self.uid}_{self.current_step}.jpg")
            obs.save(img_path)
            return img_path
        else:
            return None
    def _save_log(self):
        with open(os.path.join(self.log_path, f"{self.uid}.json"), "w") as f:
            json.dump(self.log, f, indent=2)

    def run(self):
        obs = self.env.reset()
        if self.verbose:
            cprint(f"Task: {self.task_prompt}", "blue")
        while True:
            img_path = self._save_img(obs)
            cprint(f"Step {self.current_step}, Query the Agent...", "green")
            action, actor_info = self.agent.act(self.task_prompt, img_path)
            if self.verbose:
                cprint(f"Agent: {actor_info}\n Actual Action: {action}", "blue")
            next_obs, terminated, action_success, info = self.env.step(action)
            this_step_info = {
                "step": self.current_step,
                "obs": img_path,
                "action": str(action),
                "actor_info": actor_info,
                "action_success": action_success,
                "info": info,
                "task": self.task_prompt,
            }
            if self.verbose:
                if action_success:
                    cprint(f"Action Success!", "green")
                else:
                    cprint(f"Action Failed!\n{info}", "red")
                # cprint(f"Info: {this_step_info}", "black")
            self.log.append(this_step_info)
            self._save_log()
            self.current_step += 1
            obs = next_obs 
            if terminated or not action_success:
                with open(f"{self.log_path}/log.json", "r") as f:
                    log = json.load(f)
                if self.task_prompt not in log:
                    log[self.task_prompt] = {}
                log[self.task_prompt][self.uid] = "SUCCESS" if action_success else "FAILED"
                with open(f"{self.log_path}/log.json", "w") as f:
                    json.dump(log, f, indent=2)
                break