import base64
from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image
import os
import json
import re
import random

def extract_eval_results(merged_log: str):
    """Extract the evaluation results from the merged log file."""
    results = {}
    for line in merged_log.splitlines():
        if '[Result]' in line:
            # Extract the result status (PASS/FAIL)
            result_status = 'PASS' if '(PASS)' in line else 'FAIL'

            # Extract the index from the file name
            match = re.search(r'/(\d+)\.json', line)
            if match:
                index = match.group(1)
                results[index] = result_status == 'PASS'
    return results

def extract_intent_from_text(html_content: str):
    """Extract the intent line from HTML content."""
    # Split the HTML content into lines
    lines = html_content.splitlines()
    
    # Search for the line that starts with "intent:"
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith("intent:"):
            return stripped_line.replace("intent:", "").strip()

    return ""

def extract_trajectory_info(html_content: str):
    """Extract intent and Base64 encoded images from HTML content."""
    # Parse the HTML content
    parsed_action_search = re.search(r"<div class='parsed_action'.*?><pre>stop \[(.*?)\]</pre></div>", html_content, re.DOTALL)

    # Extract the content inside the brackets
    response = parsed_action_search.group(1) if parsed_action_search else None
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Extract intent from <h2> or <h3> tags
    intent = extract_intent_from_text(html_content)
    
    # Find all image tags with src attributes
    image_tags = soup.find_all("img", src=True)
    
    # Extract Base64 encoded images and convert to PIL Image objects
    images = []
    for img in image_tags:
        if img["src"].startswith("data:image/"):
            img_data = img["src"].split(",")[1]
            byte_data = base64.b64decode(img_data)
            image = Image.open(BytesIO(byte_data))
            images.append(image)

    # Extract parsed actions
    actions = re.findall(r"<div class='parsed_action'.*?<pre>(.*?)</pre>", html_content, re.DOTALL)
    
    return {"intent": intent, "images": images, "response": response, "actions": actions}


class WebArenaData:
    def __init__(self, trajectory_root_path: str, caption_data_path: str, eval_dps_path: str, gt_results_path: str, configs_path: str = None) -> None:
        self.trajectory_root_path = trajectory_root_path
        with open(caption_data_path, 'r') as f:
            self.captions = json.load(f)
        with open(gt_results_path, 'r') as f:
            self.gt_results = json.load(f)
        with open(eval_dps_path, 'r') as f:
            self.dev_ids = json.load(f)
        
        self.config_path = configs_path
    
    def get_traj_info(self, idx):
        html_file = f"{self.trajectory_root_path}/render_{idx}.html"
        with open(html_file, 'r') as f:
            html_content = f.read()
        info = extract_trajectory_info(html_content)
        info['captions'] = self.captions[f'render_{idx}.html']
        assert len(info['captions']) == len(info['images'])
        info['traj_name'] = f'render_{idx}.html'
        if self.config_path:
            with open(self.config_path + f"/{idx}.json", 'r') as f:
                config = json.load(f)
            info['config'] = config
        return info
    
    def sample_traj_id(self, success_only=False, fail_only=False):
        if not success_only and not fail_only:
            success_only = random.choice([True, False])
        if success_only:
            id = random.choice(self.dev_ids['success'])
        else:
            id = random.choice(self.dev_ids['fail'])
        return id
    
    def get_all_samples(self):
        samples = []
        for id in self.dev_ids['success']:
            samples.append((id, True))
        for id in self.dev_ids['fail']:
            samples.append((id, False))
        return samples