def build_obs_simplifier_prompt(cap, intent, response) -> str:
    prompt = f"""Given the following user question and context, extract part of the context that is unbiased, so that using that text alone would be good context for providing an unbiased answer to the user query.

**User Query**: The bot responded with "{response}", does it execute this task "{intent}" successfully?

**Full Context**:
```md
{cap}
```

Start your answer with “Unbiased text context (includes all relevant content):"
"""
    return prompt


def build_naive_last_frame_eval_prompt(cap, intent, response) -> str:
    prompt = f"""**User Intent**: {intent}

**Bot's Final Observation**:

```md
{cap}
```    

**Bot's response to the user**: {response if response else "None"}.

---

Based on the provided user intent, the caption of bot's final observation and its response, did the bot successfully execute the task? Please reason step by step.

Note:
- The trajectory descriptions are essentially noisy captions of the screenshots captured during bot's execution. And you should infer what actions the bot took yourself.
- You should categorize the execution into one of the three status:
    - task-possible-bot-success: The bot successfully executed the task.
    - task-possible-bot-fail: The bot failed to execute the task.
    - task-impossible: The task is impossible to execute in nature given the user intent and the environment. For example, if the user wants to buy a product that does not exist in the environment. You should carefully distinguish this from bot-fail.

Format your response as a valid json:
{{
    "thoughts": "{{Your thoughts here, discuss if and how the trajectory progress towards the task and then reason about the final status. You should provide an explicit reason when determining the final status.}}",
    "status": "task-possible-bot-success" or "task-possible-bot-fail" or "task-impossible"
}}"""
    return prompt


def build_naive_multi_frame_eval_prompt(caps, intent, response) -> str:
    captions_str = "\n".join(
        [f"{idx+1}:\n```md\n{caption}\n```\n" for idx, caption in enumerate(caps[-3:])]
    )
    prompt = f"""**User Intent**: {intent}

**Bot's observation through execution**:

{captions_str}

**Bot's response to the user**: {response if response else "None"}.

---

Based on the provided user intent, bot's observation in captions and its response, did the bot successfully execute the task? Please reason step by step.

Note:
- You should categorize the execution into one of the three status:
    - task-possible-bot-success: The bot successfully executed the task.
    - task-possible-bot-fail: The bot failed to execute the task.
    - task-impossible: The task is impossible to execute in nature given the user intent and the environment. For example, if the user wants to buy a product that does not exist in the environment. You should carefully distinguish this from bot-fail.

Format your response as a valid json:
{{
    "thoughts": "{{Your thoughts here, discuss if and how the trajectory progress towards the task and then reason about the final status. You should provide an explicit reason when determining the final status.}}",
    "status": "task-possible-bot-success" or "task-possible-bot-fail" or "task-impossible"
}}"""
    return prompt


def build_naive_last_frame_eval_prompt_v2(cap, intent, response) -> tuple[str, str]:
    system_msg = (
        "You are an expert in assessing the performance of a web navigation bot, "
        "whose role is to help a human user navigate a website to complete a task. "
        "You are given the user's intent, the web page snapshots "
        "captions during the bot's execution and the bot's response to the user. "
        "Your goal is to classfiy the bot's execution in the following three cases: "
        "\n1. `task-possible-bot-success`: The bot successfully executed an achievable "
        " task. "
        "\n2. `task-possible-bot-fail`: The bot failed to execute an achievable task. "
        "\n3. `task-impossible`: The task is unachievable in natural under the "
        "condition. For example, the user wants to buy a product that does not exist "
        "in a shopping website. "
    )
    prompt = f"""The user:'s intent {intent}

The last snapshot of the web page:

```md
{cap}
```    

Bot response to the user: {response if response else "None"}.

Please reason step by step on what actions the bot may have taken, whether the final web page meets the user's requirement, etc. Note that the bot response may not be necessary for intents other than information seeking. Always try to provide an explicit reason to justify your prediction about the bot's execution status.
Format your thoughts and the final judgement in a valid json format:
{{
    "thoughts": "YOUR THOUGHTS AND REASONING PROCESS",
    "status": "task-possible-bot-success" or "task-possible-bot-fail" or "task-impossible"
}}"""
    return prompt, system_msg


def build_naive_multi_frame_eval_prompt_v2(
    caps, intent, response, num_frames=3
) -> tuple[str, str]:
    num_frames = min(num_frames, len(caps))
    frames_mention = (
        "last screen snapshot"
        if num_frames == 1
        else f"last {num_frames} screen snapshots (from earlier to later)"
    )
    captions_str = "\n".join(
        [
            f"{idx+1}:\n```md\n{caption}\n```\n"
            for idx, caption in enumerate(caps[-num_frames:])
        ]
    )
    system_msg = (
        "You are an expert in assessing the performance of a web navigation bot, "
        "whose role is to help a human user navigate a website to complete a task. "
        "You are given the user's intent, the web page snapshots "
        "captions during the bot's execution and the bot's response to the user. "
        "Your goal is to classfiy the bot's execution in the following three cases: "
        "\n1. `task-possible-bot-success`: The bot successfully executed an achievable "
        " task. "
        "\n2. `task-possible-bot-fail`: The bot failed to execute an achievable task. "
        "\n3. `task-impossible`: The task is unachievable in natural under the "
        "condition. For example, the user wants to buy a product that does not exist "
        "in a shopping website.\n\n"
        "Please reason step by step before giving the final judgement. Hints:\n"
        "(1) Infer what actions the bot may have taken by inspecting the difference between successive snapshots. "
        "(2) Take close look at the final snapshot in whether it meets the user's requirement or not. "
        "(3) The bot response may not be necessary for intents other than information seeking. "
        "(4) Always try to provide an explicit reason to justify your prediction about the bot's execution status. "
        "\n\n"
        "Format your thoughts and the final judgement in a valid json format: "
        '{"thoughts": "YOUR THOUGHTS AND REASONING PROCESS", '
        '"status": "task-possible-bot-success" or "task-possible-bot-fail" or "task-impossible"}'
    )

    prompt = f"""The user:'s intent: {intent}

The {frames_mention}:

```
{captions_str}
```    

Bot response to the user: {response if response else "None"}.

Remember to follow all the hints and format your thoughts and the final judgement in a valid json format:
{{
    "thoughts": "YOUR THOUGHTS AND REASONING PROCESS",
    "status": "task-possible-bot-success" or "task-possible-bot-fail" or "task-impossible"
}}
"""
    return prompt, system_msg


def build_obs_simplifier_prompt_v2(cap, intent, response) -> str:
    system_msg = (
        "You are an expert in extracting and summarizing key information from a "
        "web page. You are given the user's intent, and a web page snapshot "
        "caption, try to extract the most relevant information with the user intent "
        "from the caption."
    )
    prompt = f"""User intent: {intent}

Caption of the webpage snapshot:
```md
{cap}
```

Give the summarization in Markdown format similar to the caption above."
"""
    return prompt, system_msg


def build_naive_last_frame_4v_eval_prompt(intent, response) -> tuple[str, str]:
    system_msg = (
        "You are an expert in assessing the performance of a web navigation bot, "
        "whose role is to help a human user navigate a website to complete a task. "
        "You are given the user's intent, the web page snapshot at the end of bot's execution and the bot's response to the user. "
        "Your goal is to claasify the bot's execution in the following three cases: "
        "\n1. `task-possible-bot-success`: The bot successfully executed an achievable "
        " task. "
        "\n2. `task-possible-bot-fail`: The bot failed to execute an achievable task. "
        "\n3. `task-impossible`: The task is unachievable in natural under the "
        "condition. For example, the user wants to buy a product that does not exist "
        "in a shopping website. \n"
    )
    prompt = f"""The user:'s intent {intent}

The last snapshot of the web page is shown in the image.

Bot response to the user: {response if response else "None"}.

Please reason step by step on what actions the bot may have taken, whether the final web page meets the user's requirement, etc. Note that the bot response may not be necessary for intents other than information seeking. Always try to provide an explicit reason to justify your prediction about the bot's execution status.
Format your thoughts and the final judgement in a valid json format:
{{
    "thoughts": "YOUR THOUGHTS AND REASONING PROCESS",
    "status": "task-possible-bot-success" or "task-possible-bot-fail" or "task-impossible"
}}
Do not use code blocks like ``` in your response but instead start your response with {{
"""
    return prompt, system_msg


def build_final_eval_v1_prompt(cap, intent, response) -> tuple[str, str]:
    """
    This version only takes
    """
    system_msg = """You are a GUI trajectory evaluator. Given an user instruction and a description of the final state of the GUI, your goal is to classify the bot's execution into the following cases:

1. "task-impossible": The task is unachievable in nature. For example, if the goal is to buy a product that does not exist in a shopping website.
2. "task-possible-bot-success": The bot successfully executed an achievable task.
3. "task-possible-bot-fail": The bot failed to execute an achievable task.

Format your thoughts and the final judgement in json format:
{{
    "thoughts": "<your thoughts and reasoning process>",
    "status": "task-impossible", "task-possible-bot-success", or "task-possible-bot-fail"
}}

Following are some response examples:

{{
    "thoughts": "The goal is "Buy a sandwich at Burger King's website". The last snapshot shows that the bot is at the checkout page of Burger King with a sandwich in the cart, which matches the user's goal. So the bot successfully executed the task.",
    "status": "task-possible-bot-success",
}}

{{
    "thoughts": "The goal is "Cancel the 8:00am clock". The last snapshot shows that the bot is at the alarm setting page. Since there's no alarm set at 8:00am from the snapshot, the bot has already finished the task. So the bot successfully executed the task.",
    "status": "task-possible-bot-success",
}}

{{
    "thoughts": "The goal is "What's the weather today in New York?". The last snapshot shows that the weather in New York in 70F. The bot's answer is also "70F". So the bot successfully executed the task.",
    "status": "task-possible-bot-success",
}}

{{
    "thoughts": "The goal is "Find John Doe's phone number. The last snapshot shows that the bot is at John Doe's contact page. However, since John's phone number is not included in his contact page, this task is impossible to execute in nature."
    "status": "task-impossible",
}}

{{
    "thoughts": "The goal is to send a post titled \"Sharing some photo's about my cat\" to the subreddit \"cat\". The last snapshot shows the bot at the dashboard of Reddit. Since there's no evidence that the bot completed the task, the bot failed to execute the task.",
    "status": "task-possible-bot-fail",
}}

{{
    "thoughts": "The goal is to send a WhatsApp message to Sam saying "Do you want to hang out?". The last snapshot shows the bot at the message page of Sam and sent the message "Do you want to stick around? around?". Since the bot did not send the correct message, the bot failed to execute the task.",
    "status": "task-possible-bot-fail",
}}
"""
    prompt = f"""Goal: {intent}

The final state of the GUI:

```md
{cap}
```    

Bot response to the user: {response if response else "None"}.
"""
    return prompt, system_msg


def build_final_eval_v2_per_state_info_extraction_prompt(
    history, cap, prev_action, intent
) -> tuple[str, str]:
    sys_prompt = """You are a GUI agent trajectory summarizer. Given an user instruction, descriptions of bot's trajectory, its last action, the current state of the GUI post-action, your goal is to update the trajectory description with the most relevant information in this action-state pair.

Format your response into two lines as shown below

Thoughts: <your thoughts and reasoning process>
Info: <the information you want to add>

Following are some examples:

---
Instruction: Buy a sandwich at Burger King's website.
History: None
Last Action: <Omitted>
Current State: <Omitted>

Response:
Thoughts: The current state shows that it has successfully made an order at Burger King.
Info: The bot successfully made an order.

---
Instruction: Set an alarm at 4am.
History: 
1. The bot is at the homepage of Android.
2. The bot is at the clock app.
3. The bot is at the homepage.
Last Action: <Omitted>
Current State: <Omitted>

Response:
Thoughts: The current state shows the bot at the Contact app, which is not relevant to the instruction.
Info: Irrelevant.

---
Instruction: Set an alarm at 4am.
History: 
1. The bot is at the homepage of Android.
2. The bot is at the clock app.
3. The bot is at the homepage.
Last Action: <Omitted>
Current State: <Omitted>

Response:
Thoughts: The current state shows the bot at the Contact app, which is not relevant to the instruction.
Info: Irrelevant.

---
Instruction: Write a post titled "Sharing some photo's about my cat" to the subreddit "cat".
History: 
1. The bot is at subreddit "cat".
2. The bot opens a page about creating a post.
Last Action: <Omitted>
Current State: <Omitted>

Response:
Thoughts: From the current state, the bot has typed "Sharing some photo's about my cat" in the body part of the post.
Info: The bot types "Sharing some photo's about my cat" in the body part of the post.
"""
    history_str = f"\n{history}" if history is not None else "None"
    prompt = f"""Instruction: {intent}
    History: {history_str}
    Last Action: {prev_action}
    Current State:
    ```md
    {cap}
    ```"""
    return prompt, sys_prompt


def extract_content(text, start_tag):
    """
    Extract the content that follows 'Info:' in a given string.

    :param text: A string that may contain lines starting with 'Info:'
    :return: The content that follows 'Info:' or None if not found
    """
    # Split the text into lines
    lines = text.split("\n")

    # Loop through each line to find a line that starts with 'Info:'
    for line in lines:
        if line.startswith(start_tag):
            # Extract and return the content after 'Info:'
            return line[len(start_tag) :].strip()

    # Return None if 'Info:' is not found in any line
    return ""


def build_final_eval_v2_final_prompt(
    cap, intent, response, history, last_actions
) -> tuple[str, str]:
    system_msg = """You are a GUI trajectory evaluator. Given a user instruction, descriptions of bot's history trajectory and the final state of the GUI, your goal is to classify the bot's execution into the following cases:

1. "success": The bot successfully completed the task.
2. "failure": The bot hasn't completed the task.

Format your response into two lines as shown below

Thoughts: <your thoughts and reasoning process>"
Status: "success" or "failure"
"""
    prompt = f"""User instruction: {intent}

Action History:
{last_actions}

The detailed final state of the GUI:

```md
{cap}
```

Bot response to the user: {response if response else "None"}."""
    return prompt, system_msg


def build_final_eval_v3_final_prompt(
    cap, intent, response, last_actions
) -> tuple[str, str]:
    system_msg = """You are an expert in evaluating the performance of a web navigation agent. The agent is designed to help a human user navigate a website to complete a task. Given the user's intent, the agent's action history, the final state of the webpage, and the agent's response to the user, your goal is to decide whether the agent's execution is successful or not.

There are three types of tasks:
1. Information seeking: The user wants to obtain certain information from the webpage, such as the information of a product, reviews, map info, comparison of map routes, etc. The bot's response must contain the information the user wants, or explicitly state that the information is not available. Otherwise, e.g. the bot encounters an exception and respond with the error content, the task is considered a failure. Besides, be careful about the sufficiency of the agent's actions. For example, when asked to list the top-searched items in a shop, the agent should order the items by the number of searches, and then return the top items. If the ordering action is missing, the task is likely to fail.
2. Site navigation: The user wants to navigate to a specific page. Carefully examine the bot's action history and the final state of the webpage to determine whether the bot successfully completes the task. No need to consider the bot's response.
3. Content modification: The user wants to modify the content of a webpage or configuration. Carefully examine the bot's action history and the final state of the webpage to determine whether the bot successfully completes the task. No need to consider the bot's response.

*IMPORTANT*
Format your response into two lines as shown below:

Thoughts: <your thoughts and reasoning process>"
Status: "success" or "failure"
"""
    prompt = f"""User Intent: {intent}

Action History:
{last_actions}

The detailed final state of the webpage:

```md
{cap}
```

Bot response to the user: {response if response else "N/A"}."""
    return prompt, system_msg


def build_final_eval_v3_final_prompt_gpt4v(
    intent, response, last_actions
) -> tuple[str, str]:
    system_msg = """You are an expert in evaluating the performance of a web navigation agent. The agent is designed to help a human user navigate a website to complete a task. Given the user's intent, the agent's action history, the final state of the webpage, and the agent's response to the user, your goal is to decide whether the agent's execution is successful or not.

There are three types of tasks:
1. Information seeking: The user wants to obtain certain information from the webpage, such as the information of a product, reviews, map info, comparison of map routes, etc. The bot's response must contain the information the user wants, or explicitly state that the information is not available. Otherwise, e.g. the bot encounters an exception and respond with the error content, the task is considered a failure. Besides, be careful about the sufficiency of the agent's actions. For example, when asked to list the top-searched items in a shop, the agent should order the items by the number of searches, and then return the top items. If the ordering action is missing, the task is likely to fail.
2. Site navigation: The user wants to navigate to a specific page. Carefully examine the bot's action history and the final state of the webpage to determine whether the bot successfully completes the task. No need to consider the bot's response.
3. Content modification: The user wants to modify the content of a webpage or configuration. Carefully examine the bot's action history and the final state of the webpage to determine whether the bot successfully completes the task. No need to consider the bot's response.

*IMPORTANT*
Format your response into two lines as shown below:

Thoughts: <your thoughts and reasoning process>
Status: "success" or "failure"
"""
    prompt = f"""User Intent: {intent}

Action History:
{last_actions}

The last snapshot of the web page is shown in the image."""
    return prompt, system_msg


def build_android_prompt_gpt4v(intent, response, last_actions) -> tuple[str, str]:
    system_msg = """You are an expert in evaluating the performance of an android navigation agent. The agent is designed to help a human user navigate the device to complete a task. Given the user's intent, and the final state of the screen, your goal is to decide whether the agent has successfully completed the task or not.

*IMPORTANT*
Format your response into two lines as shown below:

Thoughts: <your thoughts and reasoning process>"
Status: "success" or "failure"
"""
    prompt = f"""User Intent: {intent}

Action History:
{last_actions}

The last snapshot of the screen is shown in the image.

Bot response to the user: {response if response else "N/A"}. 
"""
    return prompt, system_msg

def A_build_android_prompt(cap, sec_cap, intent, response, last_actions) -> tuple[str, str]:
    system_msg = """You are an expert in evaluating the performance of an android navigation agent. The agent is designed to help a human user navigate the device to complete a task. Given the user's intent, and the last two states of the screen, your goal is to decide whether the agent has successfully completed the task or not.

*IMPORTANT*
Format your response into two lines as shown below:

Thoughts: <your thoughts and reasoning process>"
Status: "success" or "failure"
"""
    prompt = f"""User Intent: {intent}

Action History:
{last_actions}

The detailed second last state of the screen:
```md
{sec_cap}
```

The detailed final state of the screen:
```md
{cap}
```"""
    return prompt, system_msg

def build_android_prompt(cap, sec_cap, intent, response, last_actions) -> tuple[str, str]:
    system_msg = """You are an expert in evaluating the performance of an android navigation agent. The agent is designed to help a human user navigate the device to complete a task. Given the user's intent, and the state of the screen, your goal is to decide whether the agent has successfully completed the task or not.

*IMPORTANT*
Format your response into two lines as shown below:

Thoughts: <your thoughts and reasoning process>"
Status: "success" or "failure"
"""
    prompt = f"""User Intent: {intent}

Action History:
{last_actions}

The detailed final state of the screen:
```md
{cap}
```"""
    return prompt, system_msg
