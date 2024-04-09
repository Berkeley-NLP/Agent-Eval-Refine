"""Script to run end-to-end evaluation on the benchmark"""
import argparse
import glob
import json
import logging
import os
import copy
import random
import subprocess
import tempfile
import time
from pathlib import Path

import openai
import openai.error

from agent import (
    Agent,
    PromptAgent,
    TeacherForcingAgent,
    construct_agent,
)
from agent.prompts import *
from browser_env import (
    Action,
    ActionTypes,
    ScriptBrowserEnv,
    StateInfo,
    Trajectory,
    create_stop_action,
)
from browser_env.actions import is_equivalent
from browser_env.auto_login import get_site_comb_from_filepath
from browser_env.helper_functions import (
    RenderHelper,
    get_action_description,
    save_img
)
from evaluation_harness import evaluator_router
from pprint import pprint

LOG_FOLDER = "log_files"
Path(LOG_FOLDER).mkdir(parents=True, exist_ok=True)
LOG_FILE_NAME = f"{LOG_FOLDER}/log_{time.strftime('%Y%m%d%H%M%S', time.localtime())}_{random.randint(0, 10000)}.log"

logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

file_handler = logging.FileHandler(LOG_FILE_NAME)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

# Set the log format
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)


def config() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run end-to-end evaluation on the benchmark"
    )
    parser.add_argument(
        "--render", action="store_true", help="Render the browser"
    )
    parser.add_argument(
        "--slow_mo",
        type=int,
        default=0,
        help="Slow down the browser by the specified amount",
    )
    parser.add_argument(
        "--action_set_tag", default="id_accessibility_tree", help="Action type"
    )
    parser.add_argument(
        "--observation_type",
        choices=["accessibility_tree", "html", "image"],
        default="accessibility_tree",
        help="Observation type",
    )
    parser.add_argument(
        "--current_viewport_only",
        action="store_true",
        help="Only use the current viewport for the observation",
    )
    parser.add_argument("--viewport_width", type=int, default=1280)
    parser.add_argument("--viewport_height", type=int, default=720)
    parser.add_argument("--save_trace_enabled", action="store_true")
    parser.add_argument("--sleep_after_execution", type=float, default=0.0)

    parser.add_argument("--max_steps", type=int, default=30)

    # agent config
    parser.add_argument("--agent_type", type=str, default="reflexion", choices=["reflexion"])
    parser.add_argument(
        "--instruction_path",
        type=str,
        default="agent/prompts/jsons/p_cot_id_actree_2s_reflexion.json",
    )
    parser.add_argument(
        "--parsing_failure_th",
        help="When concesecutive parsing failure exceeds this threshold, the agent will stop",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--repeating_action_failure_th",
        help="When concesecutive repeating action exceeds this threshold, the agent will stop",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--max_num_attempts",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--reflexion_evaluator",
        type=str,
        default="oracle",
        choices=["oracle", "model"],
    )

    # lm config
    parser.add_argument("--provider", type=str, default="openai")
    parser.add_argument("--model", type=str, default="gpt-3.5-turbo-0613")
    parser.add_argument("--mode", type=str, default="chat")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top_p", type=float, default=0.9)
    parser.add_argument("--context_length", type=int, default=0)
    parser.add_argument("--max_tokens", type=int, default=384)
    parser.add_argument("--stop_token", type=str, default=None)
    parser.add_argument(
        "--max_retry",
        type=int,
        help="max retry times to perform generations when parsing fails",
        default=1,
    )
    parser.add_argument(
        "--max_obs_length",
        type=int,
        help="when not zero, will truncate the observation to this length before feeding to the model",
        default=1920,
    )
    parser.add_argument(
        "--model_endpoint",
        help="huggingface model endpoint",
        type=str,
        default="",
    )
    parser.add_argument(
        "--eval_lm_model",
        type=str,
        default="mixtral",
        choices=["gpt-3.5", "gpt-4", "mixtral", "gpt-4v"],
    )
    parser.add_argument(
        "--eval_prompt_version",
        type=str,
        default="final-v3",
        choices=["final-v2", "final-v3", "final-v3-gpt4v"],
    )
    parser.add_argument(
        "--eval_status_for_reflexion",
        type=str,
        default="language",
        choices=["binary", "language"],
    )

    # example config
    parser.add_argument("--test_start_idx", type=int, default=0)
    parser.add_argument("--test_end_idx", type=int, default=1000)
    parser.add_argument("--test_indexes", type=int, nargs="+", default=[])
    parser.add_argument("--test_file", type=str, default="")

    # logging related
    parser.add_argument("--result_dir", type=str, default="")
    parser.add_argument("--baseline_dir", type=str, default="")
    args = parser.parse_args()

    # check the whether the action space is compatible with the observation space
    if (
        args.action_set_tag == "id_accessibility_tree"
        and args.observation_type != "accessibility_tree"
    ):
        raise ValueError(
            f"Action type {args.action_set_tag} is incompatible with the observation type {args.observation_type}"
        )

    return args


def early_stop(
    trajectory: Trajectory, max_steps: int, thresholds: dict[str, int]
) -> tuple[bool, str]:
    """Check whether need to early stop"""

    # reach the max step
    num_steps = (len(trajectory) - 1) / 2
    if num_steps >= max_steps:
        return True, f"Reach max steps {max_steps}"

    last_k_actions: list[Action]
    action_seq: list[Action]

    # Case: parsing failure for k times
    k = thresholds["parsing_failure"]
    last_k_actions = trajectory[1::2][-k:]  # type: ignore[assignment]
    if len(last_k_actions) >= k:
        if all(
            [
                action["action_type"] == ActionTypes.NONE
                for action in last_k_actions
            ]
        ):
            return True, f"Failed to parse actions for {k} times"

    # Case: same action for k times
    k = thresholds["repeating_action"]
    last_k_actions = trajectory[1::2][-k:]  # type: ignore[assignment]
    action_seq = trajectory[1::2]  # type: ignore[assignment]

    if len(action_seq) == 0:
        return False, ""

    last_action: Action = action_seq[-1]

    if last_action["action_type"] != ActionTypes.TYPE:
        if len(last_k_actions) >= k:
            if all(
                [
                    is_equivalent(action, last_action)
                    for action in last_k_actions
                ]
            ):
                return True, f"Same action for {k} times"

    else:
        # check the action sequence
        if (
            sum([is_equivalent(action, last_action) for action in action_seq])
            >= k
        ):
            return True, f"Same typing action for {k} times"

    return False, ""


def test(
    args: argparse.Namespace,
    agent: Agent | PromptAgent | TeacherForcingAgent,
    config_file_list: list[str],
) -> None:
    scores = []

    results = {}
    
    max_steps = args.max_steps
    assert args.agent_type == "reflexion"
    max_num_attempts = args.max_num_attempts

    early_stop_thresholds = {
        "parsing_failure": args.parsing_failure_th,
        "repeating_action": args.repeating_action_failure_th,
    }

    env = ScriptBrowserEnv(
        headless=not args.render,
        slow_mo=args.slow_mo,
        observation_type=args.observation_type,
        current_viewport_only=args.current_viewport_only,
        viewport_size={
            "width": args.viewport_width,
            "height": args.viewport_height,
        },
        save_trace_enabled=args.save_trace_enabled,
        sleep_after_execution=args.sleep_after_execution,
    )
    for config_file in config_file_list:
        # with open(config_file) as f:
        #     cfg = json.load(f)
        # if "map" in cfg["sites"]:
        #     logger.info("Skip map domain: " + config_file)
        #     continue
        render_helper = None
        try:
            meta_data = {
                "action_history": ["None"],
                "memory": []
            }

            # iterate over the max_num_attempts
            for trail_idx in range(max_num_attempts):
                render_save_dir = Path(args.result_dir) / "renders"
                if not render_save_dir.exists():
                    render_save_dir.mkdir(parents=True)
                record_save_dir = Path(args.result_dir) / "records"
                if not record_save_dir.exists():
                    record_save_dir.mkdir(parents=True)

                # get intent
                with open(config_file) as f:
                    _c = json.load(f)
                    intent = _c["intent"]
                    task_id = _c["task_id"]
                    # automatically login
                    if _c["storage_state"]:
                        cookie_file_name = os.path.basename(_c["storage_state"])
                        comb = get_site_comb_from_filepath(cookie_file_name)
                        temp_dir = tempfile.mkdtemp()
                        # subprocess to renew the cookie
                        subprocess.run(
                            [
                                "python",
                                "browser_env/auto_login.py",
                                "--auth_folder",
                                temp_dir,
                                "--site_list",
                                *comb,
                            ]
                        )
                        _c["storage_state"] = f"{temp_dir}/{cookie_file_name}"
                        assert os.path.exists(_c["storage_state"]), _c["storage_state"]
                        # update the config file
                        config_file = f"{temp_dir}/{os.path.basename(config_file)}"
                        with open(config_file, "w") as f:
                            json.dump(_c, f)
                
                if task_id not in results:
                    results[task_id] = {"intent": intent, "trails": []}
                

                logger.info(f"[Config file]: {config_file}")
                logger.info(f"[Intent]: {intent}")
                logger.info(f"#### Start trail: {trail_idx}")

                # See whether there is a baseline experiment and the result can be directly used
                baseline_dir = args.baseline_dir
                baseline_records = {}
                baseline_reflections = []
                if baseline_dir:
                    # load the baseline records
                    baseline_file = f"{baseline_dir}/records/{task_id}_{trail_idx}.json"
                    if os.path.exists(baseline_file):
                        with open(baseline_file) as f:
                            baseline_records = json.load(f)
                        logger.info(f"Loaded a baseline record from {baseline_file}")
                        # also copy the render file to the target directory
                        src_render_file = f"{baseline_dir}/renders/render_{task_id}_{trail_idx}.html"
                        dst_render_file = f"{args.result_dir}/renders/render_{task_id}_{trail_idx}.html"
                        assert os.path.exists(src_render_file), src_render_file
                        if src_render_file != dst_render_file:
                            os.system(f"cp {src_render_file} {dst_render_file}")
                    baseline_memory_file = f"{baseline_dir}/memory/memory_{task_id}.json"
                    if os.path.exists(baseline_memory_file):
                        with open(baseline_memory_file) as f:
                            baseline_memory = json.load(f)
                        baseline_reflections = baseline_memory["memory"]

                trajectory: Trajectory = []
                if baseline_records:
                    # use the baseline and no need to rerun
                    records = copy.deepcopy(baseline_records)

                else:
                    render_helper = RenderHelper(
                        config_file, render_save_dir, args.action_set_tag, trail_idx
                    )
                    # reset the records
                    records = {
                        "uid": task_id,
                        "trail_idx": trail_idx,
                        "memory": meta_data["memory"],
                        "intent": intent,
                        "response": "",
                        "steps": [],
                        "other": {"config": _c},
                    }

                    agent.reset(config_file)
                    obs, info = env.reset(options={"config_file": config_file})
                    state_info: StateInfo = {"observation": obs, "info": info}
                    trajectory.append(state_info)
                    
                    step_idx = 0
                    img_name = save_img(obs["image"], Path(args.result_dir) / "images", task_id, step_idx, trail_idx)
                    records["steps"].append(
                        {
                            "img": img_name, 
                            "accessibility_tree": obs["text"], 
                            "url": info["page"].url
                        }
                    )

                    meta_data["action_history"] = ["None"]
                    while True:
                        early_stop_flag, stop_info = early_stop(
                            trajectory, max_steps, early_stop_thresholds
                        )

                        if early_stop_flag:
                            action = create_stop_action(f"Early stop: {stop_info}")
                        else:
                            try:
                                action = agent.next_action(
                                    trajectory, intent, meta_data=meta_data
                                )
                            except ValueError as e:
                                # get the error message
                                action = create_stop_action(f"ERROR: {str(e)}")

                        trajectory.append(action)

                        action_str = get_action_description(
                            action,
                            state_info["info"]["observation_metadata"],
                            action_set_tag=args.action_set_tag,
                            prompt_constructor=agent.prompt_constructor
                            if isinstance(agent, PromptAgent)
                            else None,
                        )
                        render_helper.render(
                            action, state_info, meta_data, args.render_screenshot
                        )
                        meta_data["action_history"].append(action_str)
                        records["steps"][-1]["other"] = {"raw_action": action_str}

                        if action["action_type"] == ActionTypes.STOP:
                            break
                        
                        obs, _, terminated, _, info = env.step(action)
                        state_info = {"observation": obs, "info": info}
                        trajectory.append(state_info)

                        step_idx += 1
                        img_name = save_img(obs["image"], Path(args.result_dir) / "images", task_id, step_idx, trail_idx)
                        records["steps"].append(
                            {
                                "img": img_name, 
                                "accessibility_tree": obs["text"], 
                                "url": info["page"].url
                            }
                        )

                        if terminated:
                            # add a action place holder
                            trajectory.append(create_stop_action(""))
                            records["steps"][-1]["other"] = {"raw_action": "stop []"}
                            break
                    
                    evaluator = evaluator_router(config_file)
                    oracle_score = evaluator(
                        trajectory=trajectory,
                        config_file=config_file,
                        page=env.page,
                        client=env.get_page_client(env.page),
                    )
                    
                    records["response"] = action['answer']
                    records["oracle_score"] = oracle_score

                ### END OF TRAIL ###
                # start reflection
                if args.reflexion_evaluator == "oracle":
                    score_source = "gt"
                    score = records["oracle_score"]
                    status = "PASSED" if score == 1 else "FAILED"
                    logger.info(f"[Trail {trail_idx}] GT eval: {score} | {status}")
                else:
                    print("Running GAE evaluation ...")
                    score_source = "gae-nl"
                    score, status = agent.evaluator(records)
                    if args.eval_status_for_reflexion == "binary":
                        score_source = "gae-binary"
                        status = "PASSED" if score == 1 else "FAILED"
                    logger.info(f"[Trail {trail_idx}] GAE eval: {score} | {status}")
                
                    # save the captions to the original baseline records
                    if args.baseline_dir and os.path.exists(baseline_file):
                        with open(baseline_file, "w") as f:
                            json.dump(records, f, indent=4)
                
                records["score"] = score
                records["status"] = status
                records["score_source"] = score_source
                # pprint(records)

                # save the records
                with open(record_save_dir / f"{task_id}_{trail_idx}.json", "w") as f:
                    json.dump(records, f, indent=4)
                
                results[task_id]["trails"].append({
                    "trail_idx": trail_idx,
                    "response": records["response"],
                    "score": score,
                    "oracle_score": records["oracle_score"],
                    "status": status,
                })

                # early stop if succeed
                if score == 1:
                    break
                
                # no need to reflect for the last trail
                if trail_idx == (max_num_attempts - 1):
                    break
                
                # add a reflection to be used in the next trail
                if len(baseline_reflections) > trail_idx and baseline_records["status"] == status:
                    print("Reuse the reflection from baseline")
                    reflection = baseline_reflections[trail_idx]
                else: 
                    print("Generating a reflection ...")
                    reflection = agent.generate_reflection(records)
                meta_data["memory"].append(reflection)


            ### END OF TASK ###
            
            if not trajectory:
                # if the final trajectory is obtained from the baseline
                score = records["oracle_score"]
            else:
                # evaluate the final, fresh trajectory
                evaluator = evaluator_router(config_file)
                score = evaluator(
                    trajectory=trajectory,
                    config_file=config_file,
                    page=env.page,
                    client=env.get_page_client(env.page),
                )

                if args.save_trace_enabled:
                    env.save_trace(
                        Path(args.result_dir) / "traces" / f"{task_id}.zip"
                    )

            scores.append(score)
            if score == 1:
                logger.info(f"[Result] (PASS) {config_file}")
            else:
                logger.info(f"[Result] (FAIL) {config_file}")

            
            # save the memory
            memory_save_dir = Path(args.result_dir) / "memory"
            if not memory_save_dir.exists():
                memory_save_dir.mkdir(parents=True)
            with open(f"{memory_save_dir}/memory_{task_id}.json", "w") as f:
                memory_save = {
                    "memory": meta_data["memory"],
                    "score": score
                }
                json.dump(memory_save, f, indent=4)
            
            results[task_id]["score"] = score
            results[task_id]["final_trail_idx"] = trail_idx

        except openai.error.OpenAIError as e:
            logger.info(f"[OpenAI Error] {repr(e)}")
        except Exception as e:
            logger.info(f"[Unhandled Error] {repr(e)}]")
            import traceback

            # write to error file
            with open(Path(args.result_dir) / "error.txt", "a") as f:
                f.write(f"[Config file]: {config_file}\n")
                f.write(f"[Unhandled Error] {repr(e)}\n")
                f.write(traceback.format_exc())  # write stack trace to file

        if render_helper is not None:
            render_helper.close()

    env.close()

    if scores:
        logger.info(f"Average score: {sum(scores) / len(scores)}")

        result_fn = f"results_{args.max_num_attempts}.json"
        if os.path.exists(Path(args.result_dir) / result_fn):
            with open(Path(args.result_dir) / result_fn) as f:
                existing_results = json.load(f)
            existing_results.update(results)
            results = existing_results

        with open(Path(args.result_dir) / result_fn, "w") as f:
            json.dump(results, f, indent=4)


def prepare(args: argparse.Namespace) -> None:
    # convert prompt python files to json
    from agent.prompts import to_json

    to_json.run()

    # prepare result dir
    result_dir = args.result_dir
    if not result_dir:
        result_dir = (
            f"cache/results_{time.strftime('%Y%m%d%H%M%S', time.localtime())}"
        )
    if not Path(result_dir).exists():
        Path(result_dir).mkdir(parents=True, exist_ok=True)
        args.result_dir = result_dir
        logger.info(f"Create result dir: {result_dir}")

    if not (Path(result_dir) / "traces").exists():
        (Path(result_dir) / "traces").mkdir(parents=True)

    # log the log file
    with open(os.path.join(result_dir, "log_files.txt"), "a+") as f:
        f.write(f"{LOG_FILE_NAME}\n")


def get_unfinished(config_files: list[str], result_dir: str, max_num_attempts: int) -> list[str]:
    # result_files = glob.glob(f"{result_dir}/traces/*.zip")
    # task_ids = [
    #     os.path.basename(f).split(".")[0].split("_")[1] for f in result_files
    # ]
    # task_ids = [os.path.basename(f).split(".")[0] for f in result_files]
    results = {}
    if os.path.exists(f"{result_dir}/results_{max_num_attempts}.json"):
        with open(f"{result_dir}/results_{max_num_attempts}.json") as f:
            results = json.load(f)
    task_ids = [task_id for task_id in results.keys() if "score" in results[task_id]]
    unfinished_configs = []
    for config_file in config_files:
        task_id = os.path.basename(config_file).split(".")[0]
        if task_id not in task_ids:
            unfinished_configs.append(config_file)
    return unfinished_configs


def dump_config(args: argparse.Namespace) -> None:
    config_file = Path(args.result_dir) / "config.json"
    if not config_file.exists():
        with open(config_file, "w") as f:
            json.dump(vars(args), f, indent=4)
            logger.info(f"Dump config to {config_file}")


if __name__ == "__main__":
    args = config()
    args.sleep_after_execution = 2.0
    prepare(args)

    test_file_list = []
    if args.test_indexes:
        assert not args.test_file, "Cannot specify both test_indexes and test_file"
        for i in args.test_indexes:
            test_file_list.append(f"config_files/{i}.json")
    elif args.test_file:
        with open(args.test_file) as f:
            test_file_list = json.load(f)
        st_idx = args.test_start_idx
        ed_idx = args.test_end_idx
        test_file_list = test_file_list[st_idx:ed_idx]
    else:
        st_idx = args.test_start_idx
        ed_idx = args.test_end_idx
        for i in range(st_idx, ed_idx):
            test_file_list.append(f"config_files/{i}.json")
    if "debug" not in args.result_dir:
        test_file_list = get_unfinished(test_file_list, args.result_dir, args.max_num_attempts)

    if len(test_file_list) == 0:
        logger.info("No task left to run")
    else:
        print(f"Total {len(test_file_list)} tasks left")
        args.render = False
        args.render_screenshot = True
        args.save_trace_enabled = True

        args.current_viewport_only = True
        dump_config(args)

        agent = construct_agent(args)
        test(args, agent, test_file_list)
