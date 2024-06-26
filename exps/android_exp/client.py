from gradio_client import Client
from PIL import Image
from env import AndroidAction, ActionType
from typing import Dict, Union
from time import sleep



from abc import ABC, abstractmethod
class AbstractAgent(ABC):
    @abstractmethod
    def act(self, task:str, image_path:str)->Union[AndroidAction, Dict]:
        pass


class CogAgent:
    def __init__(self, url, temp=0.8, top_p=0.4, top_k=10):
        self.client = Client(url)
        self.temp = temp
        self.top_p = top_p
        self.top_k = top_k

    def predict(self, text:str, image_path:str)->str:
        for _ in range(3):
            try:
                out = self.client.predict(text, image_path, self.temp, self.top_p, self.top_k)
                break
            except:
                sleep(1)
        return out

    def act(self, task:str, image_path:str)->Union[AndroidAction, Dict]:
        prompt = f'What steps do I need to take to "{task}"?(with grounding)'
        out = self.predict(prompt, image_path)
        return self._translate_action(out), {"prompt": prompt, "output": out}
    
    def _translate_action(self, raw_action):
        raw_action = raw_action.split('Grounded Operation:')[1]
        try:
            action = raw_action.split(" ")[0]
            if action == 'tap':
                numbers = raw_action.split('[[')[1].split(',')
                x = int(numbers[0])
                y = int(numbers[1].split(']]')[0])
                touch_point = (x/1000, y/1000)
                return AndroidAction(action_type=ActionType.DualPoint, touch_point=touch_point, lift_point=touch_point)
            elif "type" in action:
                text = raw_action.split('"')[1]
                return AndroidAction(action_type=ActionType.Type, typed_text=text)
            elif "press home" in raw_action:
                return AndroidAction(action_type=ActionType.GoHome)
            elif "press back" in raw_action:
                return AndroidAction(action_type=ActionType.GoBack)
            elif "press enter" in raw_action:
                return AndroidAction(action_type=ActionType.Enter)
            elif "task complete" in raw_action:
                return AndroidAction(action_type=ActionType.TaskComplete)
            elif "task impossible" in raw_action:
                return AndroidAction(action_type=ActionType.TaskImpossible)
            elif "swipe up" in raw_action:
                return AndroidAction(action_type=ActionType.DualPoint, touch_point=(0.5, 0.5), lift_point=(0.5, 0.2))
            elif "swipe down" in raw_action:
                return AndroidAction(action_type=ActionType.DualPoint, touch_point=(0.5, 0.2), lift_point=(0.5, 0.5))
            elif "swipe left" in raw_action:
                return AndroidAction(action_type=ActionType.DualPoint, touch_point=(0.8, 0.5), lift_point=(0.2, 0.5))
            elif "swipe right" in raw_action:
                return AndroidAction(action_type=ActionType.DualPoint, touch_point=(0.2, 0.5), lift_point=(0.8, 0.5))
            else:
                print(f"Action {raw_action} not supported yet.")
                return AndroidAction(action_type=ActionType.Idle)
        except Exception as e:
            print(f"Action {raw_action} Parsing Error: {e}")
            return AndroidAction(action_type=ActionType.Idle)
        

class AutoUI:
    def __init__(self, url):
        self.client = Client(url)
        self.reset_history()

    def predict(self, text:str, image_path:str)->str:
        for _ in range(3):
            try:
                out = self.client.predict(text, image_path)
                break
            except:
                sleep(1)
        return out

    @classmethod
    def to_autoui(self, act: AndroidAction):
        if act.action_type == ActionType.DualPoint:
            return f'"action_type": "DUAL_POINT", "touch_point": "[{act.touch_point[1]:.4f}, {act.touch_point[0]:.4f}]", "lift_point": "[{act.lift_point[1]:.4f}, {act.lift_point[0]:.4f}]", "typed_text": ""'
        elif act.action_type == ActionType.Type:
            return f'"action_type": "TYPE", "touch_point": "[-1.0, -1.0]", "lift_point": "[-1.0, -1.0]", "typed_text": "{act.typed_text}"'
        elif act.action_type == ActionType.GoBack:
            return f'"action_type": "PRESS_BACK", "touch_point": "[-1.0, -1.0]", "lift_point": "[-1.0, -1.0]", "typed_text": ""'
        elif act.action_type == ActionType.GoHome:
            return f'"action_type": "PRESS_HOME", "touch_point": "[-1.0, -1.0]", "lift_point": "[-1.0, -1.0]", "typed_text": ""'
        elif act.action_type == ActionType.Enter:
            return f'"action_type": "PRESS_ENTER", "touch_point": "[-1.0, -1.0]", "lift_point": "[-1.0, -1.0]", "typed_text": ""'
        elif act.action_type == ActionType.TaskComplete or act.action_type == ActionType.TaskImpossible:
            return f'"action_type": "STATUS_TASK_COMPLETE", "touch_point": "[-1.0, -1.0]", "lift_point": "[-1.0, -1.0]", "typed_text": ""'
        else:
            print(f"Action {act} not supported yet.")
            return ""

    def act(self, task:str, image_path:str)->Union[AndroidAction, Dict]:
        prompt = self.prepare_prompts(task)
        out = self.predict(prompt, image_path)
        translated_action = self._translate_action(out)
        self.history_acts.append(translated_action)
        return translated_action, {"prompt": prompt, "output": out}
    
    def reset_history(self):
        self.history_acts = []

    def prepare_prompts(self, task:str):
        prompt = "Previous Actions: "
        for act in self.history_acts[-8:]:
            prompt += f"{AutoUI.to_autoui(act)} "
        prompt += f"Goal: {task}</s>"
        return prompt

    def _translate_action(self, out):
        action_str = out.split("Action Decision: ")[1]
        action_type, touch_point_1, touch_point_2, lift_point_1, lift_point_2, typed_text = action_str.split(", ")
        touch_point = touch_point_1 + ", " + touch_point_2
        lift_point = lift_point_1 + ", " + lift_point_2
        try:
            action_type = action_type.split(": ")[1].strip('"')
            if action_type == 'DUAL_POINT':
                touch_point_yx = touch_point.split(": ")[1].strip('[]"')
                touch_point_yx = [float(num) for num in touch_point_yx.split(", ")]
                lift_point_yx = lift_point.split(": ")[1].strip('[]"')
                lift_point_yx = [float(num) for num in lift_point_yx.split(", ")]
                return AndroidAction(action_type=ActionType.DualPoint, touch_point=touch_point_yx[::-1], lift_point=lift_point_yx[::-1])
            elif action_type == 'TYPE':
                text = typed_text.split(": ")[1].strip('"')
                return AndroidAction(action_type=ActionType.Type, typed_text=text)
            elif action_type == 'PRESS_HOME':
                return AndroidAction(action_type=ActionType.GoHome)
            elif action_type == 'PRESS_BACK':
                return AndroidAction(action_type=ActionType.GoBack)
            elif action_type == 'PRESS_ENTER':
                return AndroidAction(action_type=ActionType.Enter)
            elif action_type == 'STATUS_TASK_COMPLETE':
                return AndroidAction(action_type=ActionType.TaskComplete)
            elif action_type == 'TASK_IMPOSSIBLE':
                return AndroidAction(action_type=ActionType.TaskImpossible)
            else:
                print(f"Action {out} not supported yet.")
                return AndroidAction(action_type=ActionType.Idle)
        except Exception as e:
            print(f"Action {out} Parsing Error: {e}")
            return AndroidAction(action_type=ActionType.Idle)