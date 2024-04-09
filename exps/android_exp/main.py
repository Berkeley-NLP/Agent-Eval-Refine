from env import AndroidEnv, AndroidAction, ActionType
from runner import Runner
from client import CogAgent, AutoUI
import argparse
import json
import os


def main(args):
    if args.agent == "cogagent":
        agent = CogAgent("https://6cbe60874cce4c4f3e<removed>/")
    elif args.agent == "autoui-large":
        agent = AutoUI("https://23e7c6268fe5a815b0<removed>/")
    elif args.agent == "autoui-base":
        # agent = AutoUI("https://b46720d1e607b54a73<removed>/")
        agent = AutoUI("https://d6be99e10fc03a8204<removed>/")
    else:
        raise NotImplementedError(f"Agent {args.agent} not supported yet.")
    task_prompt = args.task
    output_dir = args.output_dir
    if not os.path.exists(f"{output_dir}/log.json"):
        with open(f"{output_dir}/log.json", "w") as f:
            json.dump({}, f)
    with open(f"{output_dir}/log.json") as f:
        log = json.load(f)
    if task_prompt in log:
        for uid, status in log[task_prompt].items():
            if status == "SUCCESS":
                print(f'Task "{task_prompt}"" already completed.')
                return
    env = AndroidEnv(
        avd_name="Pixel_4_API_33",
        cache_avd_name="cache_Pixel_4_API_33",
        android_avd_home="/home/<user>/.android/avd",
        emulator_path="/home/<user>/Android/Sdk/emulator/emulator",
        adb_path="/home/<user>/Android/Sdk/platform-tools/adb",
    )
    runner = Runner(task_prompt, env, agent, output_dir)
    runner.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run an Android task.")
    parser.add_argument("--task", type=str, help="Task prompt to run.")
    parser.add_argument("--output_dir", type=str, help="output_path")
    parser.add_argument("--agent", type=str, help="agent type")
    args = parser.parse_args()
    main(args)
