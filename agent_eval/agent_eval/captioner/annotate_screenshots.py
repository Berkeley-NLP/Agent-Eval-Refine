# %%
from agent_eval.clients import GPT4V_Client
from PIL import Image
import os, time
import random
from tqdm import tqdm
import json
from langdetect import detect as lang_detect
import pytesseract

random.seed(42)


# %%
def get_cap(img):
    # if random.random() < 0.5:
    #     print("=")
    # else:
    #     print("-")
    if isinstance(img, str):
        img_path = img
        img = Image.open(img)
    ocr_text = pytesseract.image_to_string(img)
    if "Website" in img_path:
        lang_code = lang_detect(ocr_text)
    else:
        lang_code = "en"
    prompt = "You are an advanced GUI captioner. Please describe this GUI interface in details and don't miss anything. Your response should be hierarchical and in Markdown format. Don't do paraphrase. Don't wrap your response in a code block."
    if lang_code != "en":
        return "LANG-ERROR"
    try:
        # from IPython import embed; embed()
        out = client.one_step_chat(prompt, img)
    except Exception as e:
        print(e)
        return "ERROR"
    return out


client = GPT4V_Client(api_key="<removed>", max_tokens=2048)

screenshot_source = [("/home/<user>/data/GUI_Proj/gui_cap_dataset/images", -1)]


images_to_cap = []
for path, num in screenshot_source:
    if num == -1:
        images_to_cap += [os.path.join(path, x) for x in os.listdir(path)]
    else:
        images_to_cap += random.sample(
            [os.path.join(path, x) for x in os.listdir(path)], num
        )

caps = []


def process_image(img):
    try:
        cap = get_cap(img)[0]
        if cap == "ERROR":
            time.sleep(10)
            return {"img": img, "cap": "ERROR"}
        elif cap == "LANG-ERROR":
            return {"img": img, "cap": "LANG-ERROR"}
        else:
            return {"img": img, "cap": cap}
    except Exception as e:
        return {"img": img, "cap": "EXCEPTION"}


def save_caps(caps):
    # with open("/home/<user>/data/GUI_Proj/screenshots/v3_cap.json", 'w') as f:
    with open("/home/<user>/data/GUI_Proj/gui_cap_dataset/final.json", "w") as f:
        json.dump(caps, f, indent=2)


caps = []

from concurrent.futures import ThreadPoolExecutor, as_completed

# Adjust the max_workers based on your needs and system capabilities
from time import sleep

with ThreadPoolExecutor(max_workers=30) as executor:
    future_to_img = {executor.submit(process_image, img): img for img in images_to_cap}
    for future in tqdm(as_completed(future_to_img), total=len(images_to_cap)):
        img = future_to_img[future]
        try:
            result = future.result()
            if result["cap"] not in ["ERROR", "LANG-ERROR", "EXCEPTION"]:
                caps.append(result)
        except Exception as exc:
            print(f"{img} generated an exception: {exc}")


save_caps(caps)
