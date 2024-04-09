import os
import json
from tqdm import tqdm
from gradio_client import Client
from collections import defaultdict

def save(this_obj, file_path):
    with open(file_path, 'w') as f:
        json.dump(this_obj, f)

def predict(img_path, client):
    result = client.predict(
            img_path,	# str  in 'text' Textbox component
            api_name="/predict"
    )
    return result

def is_last_two(file_path, total_images_per_traj):
    traj_name = "_".join(file_path.split("_")[:-1])
    traj_idx = int(file_path.split("_")[-1].split(".")[0])
    return traj_idx >= total_images_per_traj[traj_name] - 2

def caption_with_ocr_sft_model(directory, save_path, client, total, worker_idx, only_last_two):
    files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    total_images_per_traj = defaultdict(int)
    for file in files:
        traj_name = "_".join(file.split("_")[:-1])
        idx = int(file.split("_")[-1].split(".")[0])
        total_images_per_traj[traj_name] = max(idx+1, total_images_per_traj[traj_name])
    files = [files[i] for i in range(len(files)) if i % total == worker_idx]
    outs = {}
    for idx, file_path in enumerate(tqdm(files)):
        try:
            if only_last_two and not is_last_two(file_path, total_images_per_traj):
                o = "SKIP, NOT LAST TWO"
            else:
                o = predict(file_path, client)
            file_name = os.path.basename(file_path)[:-4]
            outs[file_name] = o
            if idx % 5 == 0:
                save(outs, save_path)
        except:
            print(f"Error processing {file_path}")
    save(outs, save_path)

def main(args):
    from time import sleep
    while True:
        try:
            client = Client(f"http://localhost:{args.port}")
            break
        except:
            print("Waiting for server to start...")
            sleep(5)
    images_path = args.images_path
    save_path = args.output_path.replace(".json", f"_{args.idx}.json")
    total = args.total
    idx = args.idx
    caption_with_ocr_sft_model(images_path, save_path, client, total, idx, args.only_last_two)

import argparse
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--images_path", type=str)
    parser.add_argument("--output_path", type=str)
    parser.add_argument("--port", type=int)
    parser.add_argument("--idx", type=int)
    parser.add_argument("--total", type=int)
    parser.add_argument("--only-last-two", action="store_true")
    args = parser.parse_args()
    main(args)