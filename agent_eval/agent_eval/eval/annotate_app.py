import gradio as gr
from matplotlib import pyplot as plt
import math
import io
from PIL import Image
from numpy import asarray
from agent_eval.domains.unified import UniTrajectoryDataset
import time
import json
from collections import defaultdict
import os


def main(dataset_abs_path, log_name):
    annotation_log_path = dataset_abs_path + "evals/" + log_name + ".jsonl"
    Dataset = UniTrajectoryDataset(dataset_abs_path, eval_log_names=[])

    if not os.path.exists(annotation_log_path):
        with open(annotation_log_path, "w") as f:
            pass  # Create an empty file if it doesn't exist
    all_added_annotations = defaultdict(lambda: defaultdict())
    with open(annotation_log_path, "r") as f:
        for line in f:
            ann = json.loads(line)
            all_added_annotations[ann["task_uid"]][ann["user_uid"]] = ann

    def downsample_img(img, scale=4):
        return img.resize((int(img.width / scale), int(img.height / scale)))

    def plot_images_in_grid(image_list, max_columns=3, down_scale=4):
        # start_time = time.time()

        # Determine the size of the grid
        num_images = len(image_list)
        num_rows = math.ceil(num_images / max_columns)
        image_list = [downsample_img(img, down_scale) for img in image_list]

        # Determine the size of the composite image
        max_width = max(img.width for img in image_list)
        max_height = max(img.height for img in image_list)
        composite = Image.new("RGB", (max_columns * max_width, num_rows * max_height))

        # Loop through the list of images and paste them into the composite image
        for i, image in enumerate(image_list):
            row = i // max_columns
            col = i % max_columns
            composite.paste(image, (col * max_width, row * max_height))

        # Save or display the composite image as needed
        # composite.show()  # Un-comment to display the image
        # print(f"Time to plot {num_images} images: {time.time() - start_time}")
        return composite

    def _is_un_annotated(task_idx):
        task_uid = Dataset.idx_to_uid(task_idx)
        return len(all_added_annotations[task_uid]) == 0

    def submit_annotation_and_next(
        task_idx,
        task_uid,
        user_uid,
        annotation,
        comment_box,
        show_exisiting_annotations,
        only_unannotated,
    ):
        human_readable_time = time.strftime("%m-%d %H:%M:%S", time.localtime())
        print(user_uid, task_idx, human_readable_time)
        if user_uid == "" or user_uid == None:
            gr.Error("Please enter your annotator ID")
            return render_task(task_idx, user_uid, show_exisiting_annotations)
        this_ann = {
            "dataset_path": dataset_abs_path[:-1].split("/")[-1],
            "task_idx": task_idx,
            "task_uid": task_uid,
            "user_uid": user_uid,
            "annotation": annotation,
            "comment": comment_box,
        }
        all_added_annotations[task_uid][user_uid] = this_ann
        with open(annotation_log_path, "a") as f:
            f.write(json.dumps(this_ann) + "\n")

        for i in range(task_idx + 1, len(Dataset)):
            if only_unannotated and not _is_un_annotated(i):
                continue
            return render_task(i, user_uid, show_exisiting_annotations)

    def next_task(task_idx, user_uid, show_exisiting_annotations, only_unannotated):
        for i in range(task_idx + 1, len(Dataset)):
            if only_unannotated and not _is_un_annotated(i):
                continue
            return render_task(i, user_uid, show_exisiting_annotations)

    def prev_task(task_idx, user_uid, show_exisiting_annotations, only_unannotated):
        for i in range(task_idx - 1, -1, -1):
            if only_unannotated and not _is_un_annotated(i):
                continue
            return render_task(i, user_uid, show_exisiting_annotations)

    def render_task(task_idx, user_uid, show_exisiting_annotations):
        # task_idx = Dataset.uid_to_idx(task_uid)
        task = Dataset[task_idx]
        task_uid = task["traj_name"]
        task_goal = task["intent"]
        if "web" in Dataset.dataset_path:
            task_img = plot_images_in_grid(task["images"], max_columns=1, down_scale=2)
        elif "android" in Dataset.dataset_path:
            task_img = plot_images_in_grid(task["images"], max_columns=3, down_scale=2)
        else:
            task_img = plot_images_in_grid(task["images"])
        comment = (
            all_added_annotations[task_uid][user_uid]["comment"]
            if user_uid in all_added_annotations[task_uid]
            else ""
        )
        annotation = (
            all_added_annotations[task_uid][user_uid]["annotation"]
            if user_uid in all_added_annotations[task_uid]
            else ""
        )
        annotation = "Failure"
        existing_annootations = ""
        if show_exisiting_annotations:
            for uid, ann in all_added_annotations[task_uid].items():
                existing_annootations += (
                    f"{uid}: {ann['annotation']} | {ann['comment']}\n"
                )
        else:
            existing_annootations = "Not Visible"
        agent_response = task["response"]
        act_str = ""
        for idx, act in enumerate(task["actions"]):
            act_str += f"{idx+1}: {act}\n"
        return (
            task_idx,
            task_uid,
            task_goal,
            task_img,
            comment,
            annotation,
            existing_annootations,
            agent_response,
            act_str,
        )

    with gr.Blocks(title=dataset_abs_path) as demo:
        with gr.Row():
            with gr.Column(scale=1):
                task_img = gr.Image(
                    label="Goal Image", interactive=False
                )  # managed by the app
            with gr.Column(scale=1):
                with gr.Group():
                    task_idx = gr.Number(
                        value=-1, label="Task Index", precision=0
                    )  # managed by the app
                    total_task = gr.Number(
                        value=len(Dataset), label="Total task number", precision=0
                    )  # managed by the app
                    task_uid = gr.Textbox(
                        lines=1, label="Task UID", interactive=False
                    )  # managed by the app
                    task_goal = gr.Textbox(
                        lines=1, label="Goal", interactive=False
                    )  # managed by the app
                    actions_box = gr.Textbox(
                        lines=10, label="Actions", interactive=False
                    )
                    agent_response_box = gr.Textbox(
                        lines=1, label="Agent Response", interactive=False
                    )
                    existing_annootations = gr.Textbox(
                        label="Existing Annotations", interactive=False
                    )
                with gr.Group():
                    user_uid = gr.Textbox(
                        lines=1,
                        label="Annotator ID",
                        placeholder="Enter your annotator ID",
                    )
                    comment_box = gr.Textbox(lines=1, label="Optional Comments")
                    annotation = gr.Dropdown(
                        value="Failure",
                        choices=["Success", "Failure", "Unsure", "Emulator Error"],
                        label="Annotation",
                    )
                    show_exisiting_annotations = gr.Checkbox(
                        value=True, label="Show Existing Annotations"
                    )
                    only_unannotated = gr.Checkbox(
                        value=True, label="Only Show Unannotated Task"
                    )
                with gr.Group():
                    submit_and_next = gr.Button(value="Submit and Next Task")
                    # submit = gr.Button(value="Submit Annotation")
                    next = gr.Button(value="Skip to Next Task")
                    prev = gr.Button(value="Previous Task")
                    goto = gr.Button(value="Go to Task Index")
            show_exisiting_annotations.change(
                render_task,
                inputs=[task_idx, user_uid, show_exisiting_annotations],
                outputs=[
                    task_idx,
                    task_uid,
                    task_goal,
                    task_img,
                    comment_box,
                    annotation,
                    existing_annootations,
                    agent_response_box,
                    actions_box,
                ],
            )
            submit_and_next.click(
                submit_annotation_and_next,
                inputs=[
                    task_idx,
                    task_uid,
                    user_uid,
                    annotation,
                    comment_box,
                    show_exisiting_annotations,
                    only_unannotated,
                ],
                outputs=[
                    task_idx,
                    task_uid,
                    task_goal,
                    task_img,
                    comment_box,
                    annotation,
                    existing_annootations,
                    agent_response_box,
                    actions_box,
                ],
            )
            next.click(
                next_task,
                inputs=[
                    task_idx,
                    user_uid,
                    show_exisiting_annotations,
                    only_unannotated,
                ],
                outputs=[
                    task_idx,
                    task_uid,
                    task_goal,
                    task_img,
                    comment_box,
                    annotation,
                    existing_annootations,
                    agent_response_box,
                    actions_box,
                ],
            )

            prev.click(
                prev_task,
                inputs=[
                    task_idx,
                    user_uid,
                    show_exisiting_annotations,
                    only_unannotated,
                ],
                outputs=[
                    task_idx,
                    task_uid,
                    task_goal,
                    task_img,
                    comment_box,
                    annotation,
                    existing_annootations,
                    agent_response_box,
                    actions_box,
                ],
            )
            goto.click(
                render_task,
                inputs=[task_idx, user_uid, show_exisiting_annotations],
                outputs=[
                    task_idx,
                    task_uid,
                    task_goal,
                    task_img,
                    comment_box,
                    annotation,
                    existing_annootations,
                    agent_response_box,
                    actions_box,
                ],
            )
    demo.launch(share=True)


"""
python annotate_app.py --dataset /home/<user>/data/GUI_Proj/ios_traj/unified/android-cogagent-v0/ --log_name v0
python annotate_app.py --dataset /home/<user>/data/GUI_Proj/unified_datasets/ios80-cogagent-v0/ --log_name v0
python annotate_app.py --dataset /home/<user>/data/GUI_Proj/ios_traj/unified/ios20-zeroshot-v0/ --log_name v0
python annotate_app.py --dataset /home/<user>/data/GUI_Proj/unified_datasets/ios20-selftrain-v0/ --log_name v0
python annotate_app.py --dataset /home/<user>/data/GUI_Proj/filteredbc_jan24/ --log_name v0
python annotate_app.py --dataset /home/<user>/data/GUI_Proj/filteredbc_jan24/ --log_name v0
python annotate_app.py --dataset /home/<user>/data/GUI_Proj/zeroshot_deterministic_jan28/ --log_name v0
python annotate_app.py --dataset /home/<user>/data/GUI_Proj/gpt4_deterministic_jan28/ --log_name v0
python annotate_app.py --dataset /home/<user>/data/GUI_Proj/output_autoui_large/ --log_name v0


# iOS
python annotate_app.py --dataset /home/<user>/data/GUI_Proj/ios_exps/zeroshot_deterministic_jan28/ --log_name v0
python annotate_app.py --dataset /home/<user>/data/GUI_Proj/ios_exps/selftrain_jan28/ --log_name v0
python annotate_app.py --dataset /home/<user>/data/GUI_Proj/ios_exps/mistral_jan29/ --log_name v0
"""
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--log_name", type=str, default="v0")
    args = parser.parse_args()
    main(args.dataset, args.log_name)
