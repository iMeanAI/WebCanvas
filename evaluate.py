from agent.Environment.html_env.async_env import AsyncHTMLEnvironment
from evaluate import *
from agent.Plan import *
from dataclasses import dataclass

import re
import asyncio
import argparse
import logging

# universal tools
from agent.Utils.utils import *
# evaluate tools
from evaluate.evaluate_utils import run_task, read_config, read_file
from agent.Utils.utils import read_json_file
from experiment_results import get_evaluate_result

logger = logging.getLogger(__name__)

from agent.LLM.token_utils import is_model_supported


@dataclass
class ExperimentConfig:
    mode: str
    global_reward_mode: str
    planning_text_model: str
    global_reward_text_model: str
    ground_truth_mode: bool
    single_task_name: str
    config: dict
    ground_truth_data: dict
    write_result_file_path: str
    record_time: str
    file: list


def validate_config(config, observation_mode, global_reward_mode, observation_model, global_reward_model):
    task_mode = config['basic']['task_mode']
    batch_tasks_file_path = config['files']['batch_tasks_file_path']
    json_model_response = config['model']['json_model_response']
    all_json_models = config['model']['json_models']
    interaction_mode = config['steps']['interaction_mode']

    if observation_mode not in ["dom"]:
        logger.error(
            "observation mode is not correctly defined! Currently we only support DOM observation.")
        exit()

    if interaction_mode not in [True, False]:
        logger.error(
            "interaction_mode is not defined! Try to define whether you want to evaluate the agent in an interactive manner.")
        exit()

    if json_model_response and (observation_model not in all_json_models or (
            global_reward_mode != 'no_global_reward' and global_reward_model not in all_json_models)):
        logger.error("Model does not support JSON mode!")
        exit()

    if task_mode == 'batch_tasks' and not os.path.exists(batch_tasks_file_path):
        logger.error("batch_tasks_file_path not exist!")
        exit()


def get_task_range(task_mode, file, raw_data_index):
    if task_mode == "batch_tasks":
        if raw_data_index != -1:
            re_result = re.split(r'\s|,', raw_data_index)
            raw_data_start_index = int(re_result[0])
            raw_data_end_index = int(re_result[-1]) + 1
        else:
            raw_data_start_index = 0
            raw_data_end_index = len(file)
        return range(raw_data_start_index, raw_data_end_index)
    elif task_mode == "single_task":
        return range(0, 1)
    else:
        logger.error("task_mode error!")
        exit()


def log_task_info(task_index, task_name, reference_task_length, reference_evaluate_steps):
    logger.info("*" * 100)
    logger.info(f"task index: {task_index}")
    logger.info(f"task name: {task_name}")
    logger.info(f"task reference length: {reference_task_length}")
    logger.info(f"raw data annotation: {reference_evaluate_steps}")


def generate_result_file_path(config):
    return os.path.join(config["files"]["out_file_path"], "json_result")


def load_ground_truth_data(config, ground_truth_mode):
    if ground_truth_mode:
        ground_truth_file_path = config['files']['ground_truth_file_path']
        if not os.path.exists(ground_truth_file_path):
            logger.error("ground_truth_file_path not exist!")
            exit()
        return read_json_file(ground_truth_file_path)
    return None


def create_html_environment(mode):
    return AsyncHTMLEnvironment(
        mode=mode,
        max_page_length=8192,
        headless=False,
        slow_mo=1000,
        current_viewport_only=False,
        viewport_size={"width": 1080, "height": 720},
        save_trace_enabled=False,
        sleep_after_execution=0.0,
        locale="en-US",
        use_vimium_effect=True
    )


async def run_experiment(task_range, experiment_config):
    for task_index in task_range:
        task_uuid = None
        if experiment_config.config['basic']['task_mode'] == "batch_tasks":
            task = experiment_config.file[task_index]
            task_name, task_uuid, reference_task_length, reference_evaluate_steps = task
            evaluate_steps = reference_evaluate_steps
            log_task_info(task_index, task_name,
                          reference_task_length, reference_evaluate_steps)
        elif experiment_config.config['basic']['task_mode'] == "single_task":
            task_name = experiment_config.single_task_name
            reference_task_length = experiment_config.config['steps']['single_task_action_step']
            # TODO
            evaluate_steps = experiment_config.config['steps']['single_task_action_step']
            reference_evaluate_steps = None
            logger.info(f"task_name: {task_name}")

        env = create_html_environment(experiment_config.mode)
        if is_model_supported(experiment_config.planning_text_model) and is_model_supported(
                experiment_config.global_reward_text_model):
            if not os.path.exists("token_results"):
                os.makedirs("token_results")
            token_counts_filename = f"token_results/token_counts_{experiment_config.record_time}_{experiment_config.planning_text_model}_{experiment_config.global_reward_text_model}.json"

        await run_task(mode=experiment_config.mode,
                       task_mode=experiment_config.config['basic']['task_mode'],
                       task_name=task_name,
                       task_uuid=task_uuid,
                       config=experiment_config.config,
                       write_result_file_path=experiment_config.write_result_file_path,
                       reference_task_length=reference_task_length,
                       evaluate_steps=evaluate_steps,
                       reference_evaluate_steps=reference_evaluate_steps,
                       env=env,
                       global_reward_mode=experiment_config.global_reward_mode,
                       global_reward_text_model=experiment_config.global_reward_text_model,
                       planning_text_model=experiment_config.planning_text_model,
                       ground_truth_mode=experiment_config.ground_truth_mode,
                       ground_truth_data=experiment_config.ground_truth_data,
                       interaction_mode=experiment_config.config['steps']['interaction_mode'],
                       task_index=task_index,
                       record_time=experiment_config.record_time,
                       token_pricing=experiment_config.config['token_pricing'])

        await env.close()
        del env
    if is_model_supported(experiment_config.planning_text_model) and is_model_supported(experiment_config.global_reward_text_model):
        with open(token_counts_filename, 'r') as file:
            data = json.load(file)
        total_token_cost = data.get("total_token_cost", 0)

        get_evaluate_result(experiment_config.config["files"]["out_file_path"], total_token_cost)
    logger.info('\033[31mAll tasks finished!\033[0m')
    logger.info('\033[31mPress Enter to exit...\033[0m')


async def main(global_reward_mode="no_global_reward",
               planning_text_model="gpt-4-turbo",
               global_reward_text_model="gpt-4-turbo",
               single_task_name="",
               raw_data_index=-1,
               observation_mode="dom",
               ground_truth_mode=False,
               toml_path=None
               ):
    config = read_config(toml_path)
    validate_config(config, observation_mode, global_reward_mode, planning_text_model, global_reward_text_model)

    file = None
    if config['basic']['task_mode'] == "batch_tasks":
        file = read_file(file_path=config['files']['batch_tasks_file_path'])
        task_range = get_task_range(
            config['basic']['task_mode'], file, raw_data_index)
    elif config['basic']['task_mode'] == "single_task":
        task_range = get_task_range(config['basic']['task_mode'], None, -1)

    record_time = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    write_result_file_path = generate_result_file_path(config)
    ground_truth_data = load_ground_truth_data(config, ground_truth_mode)

    experiment_config = ExperimentConfig(
        mode=observation_mode,
        global_reward_mode=global_reward_mode,
        planning_text_model=planning_text_model,
        global_reward_text_model=global_reward_text_model,
        ground_truth_mode=ground_truth_mode,
        single_task_name=single_task_name,
        config=config,
        ground_truth_data=ground_truth_data,
        write_result_file_path=write_result_file_path,
        record_time=record_time,
        file=file
    )

    await run_experiment(task_range, experiment_config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the web agent in different modes.")
    parser.add_argument("--global_reward_mode",
                        choices=["dom_vision_reward", "dom_reward",
                                 "vision_reward", "no_global_reward"],
                        default="no_global_reward", help="Choose the mode of global reward.")
    parser.add_argument("--index", type=str, default=-1)
    parser.add_argument("--single_task_name", type=str,
                        default="Find Dota 2 game and add all DLC to cart in steam.")
    parser.add_argument("--planning_text_model", type=str, default="gpt-4o-mini")
    parser.add_argument("--global_reward_text_model", type=str, default="gpt-4o-mini")

    args = parser.parse_args()

    asyncio.run(main(global_reward_mode=args.global_reward_mode,
                     planning_text_model=args.planning_text_model,
                     global_reward_text_model=args.global_reward_text_model,
                     single_task_name=args.single_task_name,
                     raw_data_index=args.index
                     )
                )
