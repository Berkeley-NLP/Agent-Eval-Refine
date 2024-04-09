import os
import shutil
from dataclasses import dataclass
from typing import List, Tuple, Union
from enum import Enum
import subprocess, signal
import re
from time import sleep

from appium import webdriver
from appium.options.android import UiAutomator2Options

import base64
from PIL import Image
from io import BytesIO
from termcolor import colored, cprint

def escape_shell_text(text):
    # List of characters to escape
    chars_to_escape = ['\\','"', "'", '`', '$']
    
    # Escape the characters by adding a backslash before them
    for char in chars_to_escape:
        text = text.replace(char, '\\' + char)
    text = text.replace(" ", "%s")
    return text

def kill_all_emulators(adb_path):
    # Get the list of connected devices
    result = subprocess.run([adb_path, 'devices'], stdout=subprocess.PIPE)
    devices_output = result.stdout.decode('utf-8')
    
    # Find all emulator device names using a regular expression
    emulators = re.findall(r'emulator-\d+', devices_output)
    
    # Shut down each emulator found
    for emulator in emulators:
        subprocess.run([adb_path, '-s', emulator, 'emu', 'kill'])
        print(f'{emulator} has been shut down.')

    if not emulators:
        print("No running emulators found.")

def clone_avd(src_avd_name, tar_avd_name, android_avd_home):
    """
    Clone the source AVD to the target AVD.

    Parameters:
    - src_avd_name: The name of the source AVD folder.
    - tar_avd_name: The name of the target AVD folder.
    - android_avd_home: The path to the .android/avd directory.

    This function copies the source AVD folder and its .ini file to a new target AVD
    and updates the paths inside the .ini files accordingly.
    """

    # Paths for source and target AVD directories and .ini files
    src_avd_dir = os.path.join(android_avd_home, src_avd_name + '.avd')
    tar_avd_dir = os.path.join(android_avd_home, tar_avd_name + '.avd')
    src_ini_file = os.path.join(android_avd_home, src_avd_name + '.ini')
    tar_ini_file = os.path.join(android_avd_home, tar_avd_name + '.ini')

    # Copy the AVD folder
    shutil.copytree(src_avd_dir, tar_avd_dir)

    # Copy the .ini file and modify it for the new AVD
    with open(src_ini_file, 'r') as src_ini, open(tar_ini_file, 'w') as tar_ini:
        for line in src_ini:
            tar_ini.write(line.replace(src_avd_name, tar_avd_name))

    # Update paths inside the target AVD's .ini files
    for ini_name in ['config.ini', 'hardware-qemu.ini']:
        ini_path = os.path.join(tar_avd_dir, ini_name)
        if os.path.exists(ini_path):
            with open(ini_path, 'r') as file:
                lines = file.readlines()
            with open(ini_path, 'w') as file:
                for line in lines:
                    # Update paths and AVD name/ID
                    new_line = line.replace(src_avd_name, tar_avd_name)
                    file.write(new_line)

    # Update the snapshots' hardware.ini file if it exists
    snapshots_hw_ini = os.path.join(tar_avd_dir, 'snapshots', 'default_boot', 'hardware.ini')
    if os.path.exists(snapshots_hw_ini):
        with open(snapshots_hw_ini, 'r') as file:
            lines = file.readlines()
        with open(snapshots_hw_ini, 'w') as file:
            for line in lines:
                # Update AVD name/ID
                new_line = line.replace(src_avd_name, tar_avd_name)
                file.write(new_line)


class ActionType(Enum):
    Idle=0
    DualPoint=1
    Type=2
    GoBack=3
    GoHome=4
    Enter=5
    TaskComplete=6
    TaskImpossible=7

@dataclass
class AndroidAction():
    action_type: ActionType
    touch_point: Tuple[float, float] = None
    lift_point: Tuple[float, float] = None
    typed_text: str = None

    def __str__(self):
        # Construct the basic action type string.
        components = [f"Action Type: {self.action_type.name}"]

        # Format and add touch_point if it's not None.
        if self.touch_point:
            touch_point_str = f"({self.touch_point[0]:.4f}, {self.touch_point[1]:.4f})"
            components.append(f"Touch Point: {touch_point_str}")

        # Format and add lift_point if it's not None.
        if self.lift_point:
            lift_point_str = f"({self.lift_point[0]:.4f}, {self.lift_point[1]:.4f})"
            components.append(f"Lift Point: {lift_point_str}")

        # Add typed_text if it's not None.
        if self.typed_text:
            components.append(f"Typed Text: '{self.typed_text}'")

        # Join all components into a single string.
        return ", ".join(components)

    def to_act(self):
        pass



class AndroidEmulator():
    def __init__(self, avd_name, max_steps, emulator_path="~/Android/Sdk/emulator/emulator", appium_server_url='http://localhost:4723'):
        self.emulator_path = os.path.expanduser(emulator_path)
        self.avd_name = avd_name
        cprint(colored(f"Starting the Emulator", "green"))
        self.emulator_process = subprocess.Popen(f"{self.emulator_path} -avd {self.avd_name} -no-boot-anim -gpu auto -no-snapshot-save -no-audio -netfast -partition-size 4096 -cache-size 4000", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sleep(30)
        capabilities = dict(
            platformName='Android',
            automationName='uiautomator2',
            deviceName='Android',
            newCommandTimeout="1200"
        )
        self.options = UiAutomator2Options().load_capabilities(capabilities)
        self.appium_server_url = appium_server_url
        self.driver = webdriver.Remote(self.appium_server_url, options=self.options)
        self.terminated = False
        self.max_steps = max_steps
        self.steps = 0
        screen_size = self.driver.get_window_size()
        self.screen_size = (screen_size["width"], screen_size["height"])
    
    def terminate(self):
        self.emulator_process.terminate()
        try:
            self.emulator_process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            self.emulator_process.kill()
            self.emulator_process.wait()
    
    def refresh_driver(self):
        self.driver.quit()
        self.driver = webdriver.Remote(self.appium_server_url, options=self.options)
    
    def get_obs(self):
        screenshot_str = self.driver.get_screenshot_as_base64()
        imgdata = base64.b64decode(screenshot_str)
        image =  Image.open(BytesIO(imgdata))
        # Assuming 'image' is your PIL Image object in RGBA mode
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        return image

    def step(self, action: AndroidAction):
        self.steps += 1
        if self.steps > self.max_steps:
            action = AndroidAction(action_type=ActionType.TaskImpossible)
            cprint(colored(f"Terminate the Emulator: Max Steps Exceeded {self.max_steps}.", "red"))
        if self.terminated:
            raise Exception("The emulator is terminated.")
        screenshot = None
        info = {}
        try:
            if action.action_type == ActionType.DualPoint:
                assert len(action.touch_point) == 2
                assert len(action.lift_point) == 2
                touch_x = action.touch_point[0] * self.screen_size[0]
                touch_y = action.touch_point[1] * self.screen_size[1]
                lift_x = action.lift_point[0] * self.screen_size[0]
                lift_y = action.lift_point[1] * self.screen_size[1]
                self.driver.swipe(touch_x, touch_y, lift_x, lift_y)
            elif action.action_type == ActionType.Type:
                # This doesn't work well because of active element
                # element = self.driver.switch_to.active_element
                # try:
                #     element.send_keys(action.typed_text)
                # except Exception as e:
                #     cprint(f"Type Error: {e}", "red")
                t = escape_shell_text(action.typed_text)
                self.driver.execute_script('mobile: shell', {
                    'command': 'input',
                    'args': ['text', t],
                    'includeStderr': True,
                    'timeout': 5000
                    })
                
            elif action.action_type == ActionType.GoBack:
                self.driver.back()
            elif action.action_type == ActionType.GoHome:
                self.driver.press_keycode(3)
            elif action.action_type == ActionType.Enter:
                self.driver.press_keycode(66)
            elif action.action_type == ActionType.TaskComplete:
                self.terminated = True
            elif action.action_type == ActionType.TaskImpossible:
                self.terminated = True
            elif action.action_type == ActionType.Idle:
                pass
            else:
                raise Exception(f"Unknown action type: {action.action_type}")
            action_success = True
            screenshot = self.get_obs()
            if self.terminated:
                self.driver.quit()
                self.terminate()
        except Exception as e:
            action_success = False
            info["error"] = str(e)
            self.driver.quit()
            self.terminate()
        return screenshot, self.terminated, action_success, info

class AndroidEnv():
    """
    This class wraps around the android emulator and provides a more infrastructure for free-form GUI navigation
    """
    def __init__(self, 
                 avd_name, 
                 cache_avd_name,
        android_avd_home: str = '~/.android/avd',
         emulator_path: str = '~/Android/Sdk/emulator/emulator',
         adb_path: str = "~/Library/Android/sdk/platform-tools/adb",
         run_headless: bool = False,
         max_steps: int = 20):
        self.android_avd_home = os.path.expanduser(android_avd_home)
        self.emulator_path = os.path.expanduser(emulator_path)
        self.adb_path = os.path.expanduser(adb_path)
        self.avd_name = avd_name
        self.cache_avd_name = cache_avd_name
        self.run_headless = run_headless
        self.max_steps = max_steps
    
    def reset(self):
        """
        Reset the emulator to a clean state
        """
        # If the emulator is already running, kill it,
        # Then delete the cache AVD
        kill_all_emulators(self.adb_path)
        if hasattr(self, "emulator_process"):
            self.emulator_process.send_signal(signal.SIGINT)
            self.emulator_process.wait()
        cache_avd_path = os.path.join(self.android_avd_home, self.cache_avd_name + ".avd")
        cache_avd_ini_path = os.path.join(self.android_avd_home, self.cache_avd_name + ".ini")
        if os.path.exists(cache_avd_path):
            shutil.rmtree(cache_avd_path)
        if os.path.exists(cache_avd_ini_path):
            os.remove(cache_avd_ini_path)
        sleep(2)
        # Clone the source AVD and start the emulator
        clone_avd(self.avd_name, self.cache_avd_name, self.android_avd_home)
        self.emulator = AndroidEmulator(avd_name=self.cache_avd_name, emulator_path=self.emulator_path, max_steps=self.max_steps)
        return self.emulator.get_obs()
    
    def step(self, action):
        if not self.emulator:
            raise Exception("Please call reset() before calling step()")
        return self.emulator.step(action)