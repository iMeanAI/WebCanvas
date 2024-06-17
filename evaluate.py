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
from evaluate_utils import run_task, read_config, read_file, read_json_file


logger = logging.getLogger(__name__)

@dataclass
class ExperimentConfig:
    mode: str
    global_reward_mode: str
    observation_text_model_name: str
    global_reward_text_model_name: str
    ground_truth_mode: bool
    single_task_name: str
    config: dict
    ground_truth_data: dict
    write_result_file_path: str
    record_time: str
    file: list

def validate_config(config, mode, observation_text_model_name):
    task_mode = config['basic']['Task_Mode']
    batch_tasks_file_path = config['files']['Batch_Tasks_File_Path']
    json_model_response = config['model']['JSON_Model_Response']
    all_json_models = config['model']['All_JSON_Models']
    step_stop = config['steps']['Step_Stop']
    
    if mode not in ["dom"]:
        logger.error("observation mode is not correctly defined! Currently we only support DOM observation.")
        exit()

    if step_stop not in [True, False]:
        logger.error("step_stop is not defined! Try to define your way to terminate the agent.")
        exit()

    if json_model_response and observation_text_model_name not in all_json_models:
        logger.error("The observation text model does not support JSON mode!")
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
    logger.info(f"Start")
    logger.info(f"task index: {task_index}")
    logger.info(f"task name: {task_name}")
    logger.info(f"task reference length: {reference_task_length}")
    logger.info(f"raw data annotation: {reference_evaluate_steps}")

def generate_result_file_path(config, mode, observation_text_model_name, global_reward_mode, global_reward_text_model_name, ground_truth_mode, record_time_short, record_time):
    return f"./csv_results/raw_record_{record_time_short}/raw_record_{record_time}_{mode}_{observation_text_model_name}_{global_reward_mode}_{global_reward_text_model_name}_{ground_truth_mode}"

def load_ground_truth_data(config, ground_truth_mode):
    if ground_truth_mode:
        ground_truth_file_path = config['files']['Ground_Truth_File_Path']
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
        if experiment_config.config['basic']['Task_Mode'] == "batch_tasks":
            task = experiment_config.file[task_index]
            task_name, task_uuid, reference_task_length, reference_evaluate_steps = task
            evaluate_steps = reference_evaluate_steps
            log_task_info(task_index, task_name, reference_task_length, reference_evaluate_steps)
        elif experiment_config.config['basic']['Task_Mode'] == "single_task":
            task_name = experiment_config.single_task_name
            reference_task_length = experiment_config.config['steps']['Single_Task_Action_Step']
            evaluate_steps = experiment_config.config['steps']['Single_Task_Action_Step'] #TODO
            reference_evaluate_steps = None
            logger.info(f"task_name: {task_name}")

        env = create_html_environment(experiment_config.mode)

        await run_task(mode=experiment_config.mode,
                       task_mode=experiment_config.config['basic']['Task_Mode'],
                       task_name=task_name,
                       task_uuid=task_uuid,
                       config=experiment_config.config,
                       write_result_file_path=experiment_config.write_result_file_path,
                       reference_task_length=reference_task_length,
                       evaluate_steps=evaluate_steps,
                       reference_evaluate_steps=reference_evaluate_steps,
                       env=env,
                       global_reward_mode=experiment_config.global_reward_mode,
                       global_reward_text_model_name=experiment_config.global_reward_text_model_name,
                       observation_text_model_name=experiment_config.observation_text_model_name,
                       ground_truth_mode=experiment_config.ground_truth_mode,
                       ground_truth_data=experiment_config.ground_truth_data,
                       json_model_response=experiment_config.config['model']['JSON_Model_Response'],
                       step_stop=experiment_config.config['steps']['Step_Stop'],
                       task_index=task_index,
                       record_time=experiment_config.record_time)

        await env.close()
        del env

    print(f"\033[31mtask finished!\033[0m")
    input(f"\033[31mPress Enter to exit...\033[0m")

async def main(global_reward_mode="no_global_reward",
               observation_text_model_name="gpt-4-turbo",
               global_reward_text_model_name="gpt-4-turbo",
               single_task_name="",
               raw_data_index=-1,
               mode="dom",
               ground_truth_mode=False,
               toml_path=None
               ):

    config = read_config(toml_path)
    validate_config(config, mode, observation_text_model_name)

    file = None
    if config['basic']['Task_Mode'] == "batch_tasks":
        file = read_file(file_path=config['files']['Batch_Tasks_File_Path'])
        task_range = get_task_range(config['basic']['Task_Mode'], file, raw_data_index)
    elif config['basic']['Task_Mode'] == "single_task":
        task_range = get_task_range(config['basic']['Task_Mode'], None, -1)

    record_time_short = time.strftime("%Y%m%d", time.localtime())
    record_time = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    write_result_file_path = generate_result_file_path(config, mode, observation_text_model_name, global_reward_mode, global_reward_text_model_name, ground_truth_mode, record_time_short, record_time)
    ground_truth_data = load_ground_truth_data(config, ground_truth_mode)
    
    experiment_config = ExperimentConfig(
        mode=mode,
        global_reward_mode=global_reward_mode,
        observation_text_model_name=observation_text_model_name,
        global_reward_text_model_name=global_reward_text_model_name,
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
    parser = argparse.ArgumentParser(description="Run the web agent in different modes.")
    parser.add_argument("--global_reward_mode",
                        choices=["dom_vision_reward", "dom_reward", "vision_reward", "no_global_reward"],
                        default="dom_reward", help="Choose the mode of global reward.")
    parser.add_argument("--index", type=str, default=-1)
    parser.add_argument("--single_task_name", type=str, default="Find Dota 2 game and add all DLC to cart in steam.")
    args = parser.parse_args()

    asyncio.run(main(global_reward_mode=args.global_reward_mode,
                     observation_text_model_name="gpt-3.5-turbo",
                     global_reward_text_model_name="gpt-3.5-turbo",
                     single_task_name=args.single_task_name,
                     raw_data_index=args.index))
