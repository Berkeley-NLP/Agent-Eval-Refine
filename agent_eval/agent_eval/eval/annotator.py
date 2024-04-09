import json
import os
from typing import Any, List, Tuple

from termcolor import cprint

sys_prompt_v1_icl = """You are a GUI Trajectory Evaluator. Your task is to observe a bot's action within a graphical user interface (GUI) and classify its behavior into one of four categories based on its progress towards a specified goal. The categories are: 

1. "towards-the-goal" - The bot is moving closer to achieving the goal.
2. "not-sure" - It's unclear if the bot's actions are helping reach the goal.
3. "goal-reached" - The bot has successfully completed the goal.
4. "away-from-the-goal" - The bot's actions are diverting it from the goal.

Please format your response as follows:

Thoughts: [Explain your reasoning here]
Response: "towards-the-goal", "not-sure", "goal-reached", or "away-from-the-goal"

Here are some example responses:

---

Example 1:
Thoughts: The goal is to 'set an alarm at 8:00 am.' Initially, the bot is on the home screen. After a tap action, it navigates to the alarm app, indicating progress towards the goal.
Response: "towards-the-goal"

Example 2:
Thoughts: The goal is to 'buy the latest iPhone on Amazon.' The bot starts at the checkout page on Amazon. After a tap action, the screen shows a successful purchase, signifying that the goal has been reached.
Response: "goal-reached"

Example 3:
Thoughts: The goal is to 'show me the weather in New York.' The bot begins on London's weather page. After pressing 'home', it returns to the home screen, moving away from the goal.
Response: "away-from-the-goal"

Example 4:
Thoughts: The goal is to 'buy some coffee on the Starbucks app.' The bot begins on the Amazon app. After pressing 'back,' it moves to the home screen, which is a prerequisite for opening the Starbucks app.
Response: "towards-the-goal"

Example 5:
Thoughts: The goal is to 'open YouTube.' The bot begins on the home screen. After a swipe, it appears to remain on the same page, suggesting no progress towards the goal.
Response: "not-sure"

Note:
You should be extra-careful when assigning "goal-reached" or "towards-the-goal" labels. If you are unsure, please select "not-sure" instead. 

---
"""

def built_user_prompt_v1(intent, current_state, action, next_state):
    return f"""Goal: {intent}
Original State: 
```md
{current_state}
```
State after action: "{action}":
```md
{next_state}
```"""


class Annotator:
    def __init__(self, lm_clients, log_save_path=None):
        self.lm_clients = lm_clients
        self.log_save_path = log_save_path

    def __call__(self, info, client, version):
        assert (
            client in self.lm_clients
        ), f"Client {client} not found in {self.lm_clients.keys()}"
        client = self.lm_clients[client]
        if version == "v1":
            return self.annotate_v1(info, client)

    def annotate_v1(self, info, client):
        """
        Given a series of trajectory, return if each of the state-action pair is towards the goal.
        """
        """
        How this works:
        Given a 
        state -> action -> next_state pairs
        We classify it into:
        1. it is towards the goal
        2. not sure
        3. it completes the task
        4. it doesn't lead us closer to the goal
        """
        intent = info["intent"]
        results = []
        sys_prompt = sys_prompt_v1_icl
        # cprint(sys_prompt, "blue")
        for idx in range(len(info["captions"])):
            current_state = info["captions"][idx]
            if idx == len(info["captions"]) - 1:
                "If it's the last one, the next step is termination"
                next_state = "Terminated"
            else:
                next_state = info["captions"][idx + 1]
            action = info["actions"][idx]
            user_prompt = built_user_prompt_v1(
                intent, current_state, action, next_state
            )
            # out, _ = client.one_step_chat(text=user_prompt, system_msg=sys_prompt)
            extended_user_prompt = f"{sys_prompt}\n\n{user_prompt}"
            out, _ = client.one_step_chat(text=extended_user_prompt)
            # cprint(user_prompt, "green")
            # cprint(out, "yellow")
            results.append(out)
        return results
