import time
import os
import subprocess
import signal
import cv2
import random
from PIL import Image
import json

with open("train_tasks.json", "r") as fb:
    ALL_TASKS = json.load(fb)
TASK_PROMPT = 'What steps do I need to take to "{task}"?(with grounding)'
ALL_TASKS = [TASK_PROMPT.format(task=task) for task in ALL_TASKS]


class IOSEnv:
    def __init__(
        self,
        save_path="/Users/<user>/Desktop/idb-test/images/",
        device_path="/Users/<user>/Library/Developer/CoreSimulator/Devices",
        udid="6E44D401-6183-4F8E-9232-DD84BD9AC821",
        max_steps=10,
    ):
        """_summary_

        Args:
                save_path (str): The path where the images observations should be saved. Defaults to "/Users/<user>/Desktop/idb-test/images/".
                device_path (str): The path to the simulator devices. Defaults to "/Users/<user>/Library/Developer/CoreSimulator/Devices".
                udid (str): The udid of the simulator to be used. Defaults to "6E44D401-6183-4F8E-9232-DD84BD9AC821".
                max_steps (int, optional): maximum number of steps. Defaults to 10.
        """
        self.save_path = save_path
        # if id is not None:
        #     self.id = id
        # else:
        self.udid = udid
        self.device_path = device_path
        self.max_steps = max_steps
        self.steps = 0
        self.output_time = None

    def get_observation(self):
        time.sleep(3)
        output_path = os.path.join(
            self.save_path, f"{self.output_time}-{str(self.steps)}.jpg"
        )
        os.system(f"xcrun simctl io {self.udid} screenshot {output_path}")
        # os.system(f"idb screenshot {output_path} --udid {self.udid}")
        # # process = subprocess.Popen(["idb", "record", "video", "--udid", self.udid, output_path])
        # # # process.communicate("sleep 1")
        # # process.send_signal(signal.SIGINT)
        # # process.wait(i
        # # breakpoint()
        # # import IPython; IPython.embed()
        # os.system(f"timeout 4s idb record video --udid {self.udid} {output_path}")
        # time.sleep(2)
        # for i in range(5):
        #     try:
        #         vidcap = cv2.VideoCapture(output_path)
        #         _, image = vidcap.read()
        #         img = Image.fromarray(image)
        #         r,g,b = img.split()
        #         corrected_img = Image.merge("RGB", (b, g, r))
        #         corrected_img.save(output_path.replace("mp4", "jpg"))
        #         break
        #     except Exception as e:
        #         print(e)
        #         print("waiting for recording to complete")
        #         time.sleep(2)
        # os.system(f'rm {output_path}')
        return output_path

    def reset(self, options=None):
        # self.kill()
        self.steps = 0
        # self.udid = os.popen(f'xcrun simctl clone {self.back_udid} {self.id}').read().replace('\n', '')
        os.system(f"idb boot {self.udid}")
        os.system(f"idb set-location --udid {self.udid} 40.7128 -74.0060")
        time.sleep(10)
        self.output_time = str(time.time())
        return self.get_observation(), None

    def step(self, action):
        """
        Args:
                action (str): idb command

        creates an image in self.save_path of current observation
        Returns:
                obs (str): the relative path in self.save_path for the image
        """
        assert self.steps < self.max_steps
        self.steps += 1
        reward = 0
        if action == "end":
            self.steps = self.max_steps  # set time limit to end the episode
        else:
            os.system(action.format(udid=self.udid))
        time.sleep(1)
        obs = self.get_observation()
        done = self.steps >= self.max_steps
        if done:
            self.kill()
        return obs, reward, done, {}

    def kill(self):
        """
        Kill the idb process and reset the environment
        """
        # print("killing")
        os.system(f"idb shutdown {self.udid}")
        # restore to initial state
        # breakpoint()
        os.system(f"rm -r {os.path.join(self.device_path, self.udid)}")
        os.system(
            f"cp -rH {os.path.join(self.device_path, 'back')} {os.path.join(self.device_path, self.udid)}"
        )

    # def kill(self):
    #     """


# 	Kill the idb process and reset the environment
# 	"""
#     # print("killing")
#     os.system(f"idb shutdown {self.udid}")
#     os.system(f"xcrun simctl delete {self.udid}")
#     # #restore to initial state
#     # os.system(f"rm -r {os.path.join(self.device_path, self.udid)}")
#     # os.system(f"cp -rH {os.path.join(self.device_path, 'back')} {os.path.join(self.device_path, self.udid)}")
