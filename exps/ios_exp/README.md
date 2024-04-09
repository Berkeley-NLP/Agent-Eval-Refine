# IOS Evaluation Experiment
## Environment Setup
Install packages
```
pip install opencv-python Pillow tqdm gradio
#Install IOS Debug Bridge
brew tap facebook/fb
brew install idb-companion
pip install fb-idb
```
Setup the ios emulator (Apple devices required)
- Download Xcode and create a new Simulator with `IPhone 14, IOS 14.2, not paired with Apple Watch`
- Open the apps, `Map`, `Calendar`, `Photos`, `Reminders`, `News`, `Maps`, `Health`, `Wallet`, `Settings`, `Safari`, `Messages`, `Watch`, `Contacts`, `Files`, `Shortcuts`, `Freeform`, click `allow while using app` for all location permission and allow notifications, click `not now` for icloud syncing requests.
- Check the UDID of the new simulator by running `idb list-targets`
- Set the location by `idb set-location  —udid {UDID} 40.7128 -74.0060`
- cd into `/Users/{UserName}/Library/Developer/CoreSimulator/Devices` and run `cp -rH {UDID} back` to save this state



## Run the agents
**Inference Server for CogAgent**
1. Visit [CogAgent's Official Repo](https://github.com/THUDM/CogVLM) and follow the instructions to install the dependencies.
2. Copy `models/CogAgent/web_demo_simple.py` from current folder into `CogVLM/basic_demo/` folder.
3. Run `python web_demo_simple.py` to start the server.

**Run the Agent on IOS to Collect Trajectories**
```
python collect_trajectories.py --udid {UDID} --output-path {xx.json} --gardio-http {gradio_link}
```

**Improve the Agent through Filtered BC**

Please first annotate the collected trajectories with our evaluator, please refer to the Evaluation Section in Main README for more details.

Then, select of state-action pairs with positive rewards and use it to finetune the CogAgent model. We use CogAgent's official repo to finetune the model. 
The weights we used are available at [Huggingface Hub](https://huggingface.co/Agent-Eval-Refine).