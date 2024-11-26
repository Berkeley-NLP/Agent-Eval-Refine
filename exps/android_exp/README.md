# Android Evaluation Experiment
## Environment Setup
Install packages
```
sudo npm i --location=global appium
appium driver install uiautomator2
pip install Appium-Python-Client
```
Setup the android enumlator
- Download Android studio and start a `Pixel 4 Android 13.0 API 33` Device from Android Studio - Virtual Device Manager
- Register and log into the new google account named `Alex`
- Add 6 images to google photos
- Delete image 6
- Set GPS location to `37.871666, -122.272781` (Berkeley Way West)
- Send a message to jiayidotpan@gmail.com
    - Title “Wanna have a lunch?”
    - Descrption:
    - “Hey, wanna have a lunch together tomorror?”
- Open all installed apps, allow notications/other permissions. For google apps, sign in, do not backup
- Connect Appium to it
- Clean background process
A few extra steps to make the emulator reproducible
- Go to `~/.android/avd` and copy avd folder of AVD you want to clone
- Also copy `.ini` file of this AVD, open .ini file and change all paths to the new folder you have created
Go to the new folder; open the `.ini` file and change its paths, too



## Run the agents
**Inference Server for CogAgent**
1. Visit [CogAgent's Official Repo](https://github.com/THUDM/CogVLM) and follow the instructions to install the dependencies.
2. Copy `models/CogAgent/web_demo_simple.py` from current folder into `CogVLM/basic_demo/` folder.
3. Run `python web_demo_simple.py --fp16` to start the server.

**Inference Server for Auto-UI**
<!-- exps/android_exp/models/Auto-UI/README.md -->
Please refer to [`exps/android_exp/models/Auto-UI/README.md`](exps/android_exp/models/Auto-UI/README.md) for instructions on how to run the Auto-UI model.

**Run the Agent on Android**
Please copy the gradio link obtained from either CogAgent or Auto-UI and paste it in the `main.py`.

Then select the command to run the agent:
```
./run_all.sh # for running all agents
./run_cogagent.sh # for running CogAgent
./run_autoui_base.sh # for running Auto-UI
./run_autoui_large.sh # for running Auto-UI Large
```
