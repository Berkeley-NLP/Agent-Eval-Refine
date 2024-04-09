from gradio_client import Client
import argparse
from env import IOSEnv, ALL_TASKS
from utils import translate_action
from tqdm import tqdm
import json

import random


def main(args):
    client = Client(args.gardio_http)
    env = IOSEnv(save_path=args.save_path, udid=args.udid, device_path=args.device_path)
    episodes = []
    for _ in range(1):
        random.shuffle(ALL_TASKS)
        for current_task in tqdm(ALL_TASKS):
            while True:
                try:
                    episode = []
                    obs, _ = env.reset()
                    done = False
                    while not done:
                        raw_action = client.predict(
                            current_task, obs, 1.5, 1, 100, api_name="/predict"
                        )

                        translated_action, idb_action = translate_action(raw_action)
                        next_obs, _, done, _ = env.step(idb_action)
                        episode.append(
                            {
                                "observation": obs,
                                "raw_action": raw_action,
                                "translated_action": translated_action,
                                "idb_action": idb_action,
                                "next_observation": next_obs,
                                "done": done,
                                "task": current_task,
                            }
                        )
                        obs = next_obs
                    episodes.append(episode)
                    with open(args.output_path, "w") as fb:
                        json.dump(episodes, fb)
                    break
                except ValueError:
                    print("error")
                    env.kill()
                    continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gardio-http", default="https://a66ecf765b66e00e21<removed>/")
    parser.add_argument(
        "--udid", default="16199A9E-A005-449E-92B1-10755C359799", type=str
    )
    parser.add_argument(
        "--save-path",
        default="/Users/<user>/Desktop/idb-test/zeroshot_train/images/",
        type=str,
    )
    parser.add_argument(
        "--device-path",
        default="/Users/<user>/Library/Developer/CoreSimulator/Devices",
        type=str,
    )
    parser.add_argument("--output-path", type=str)
    args = parser.parse_args()
    main(args)
