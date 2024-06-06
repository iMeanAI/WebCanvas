from agent.Environment.html_env.async_env import AsyncHTMLEnvironment, ActionExecutionError
from evaluate import *
from agent.Plan import *
from playwright.async_api import Playwright, async_playwright, expect, Page
from agent.Environment.html_env.actions import create_action, Action, ActionTypes

import re
import asyncio
import argparse
import toml

# universal tools
from agent.Utils.utils import *
# evaluate tools
from evaluate_utils import *


async def main(global_reward_mode="no_global_reward",
               observation_text_model_name="gpt-4-turbo",
               global_reward_text_model_name="gpt-4-turbo",
               single_task_name="",
               raw_data_index=-1,
               mode="dom",
               ground_truth_mode=False,
               setting_toml_path=""
               ):
    if setting_toml_path:
        # Use the specified path
        config = read_config('path/to/your/setting.toml')
    else:
        # Use the default path
        config = read_config()

    task_mode = config['basic']['Task_Mode']
    batch_tasks_file_path = config['files']['Batch_Tasks_File_Path']
    json_model_response = config['model']['JSON_Model_Response']
    all_json_models = config['model']['All_JSON_Models']
    step_stop = config['steps']['Step_Stop']
    if mode not in ["dom"]:
        logger.error("observation mode error!")
        exit()

    if step_stop not in [True, False]:
        logger.error("step_stop error!")
        exit()

    if json_model_response:
        if observation_text_model_name not in all_json_models:
            logger.error("The observation text model does not support JSON mode!")
            exit()
        elif observation_text_model_name in all_json_models:
            print("The observation text model are using JSON mode!")

    if not os.path.exists(batch_tasks_file_path):
        logger.error("batch_tasks_file_path not exist!")
        exit()

    if task_mode == "batch_tasks":
        # result record for batch_tasks
        record_time_short = time.strftime("%Y%m%d", time.localtime())
        record_time = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        write_result_file_path = f"./csv_results/raw_record_{record_time_short}/raw_record_{record_time}_{mode}_{observation_text_model_name}_{global_reward_mode}_{global_reward_text_model_name}_{ground_truth_mode}"
        file = read_file(file_path=batch_tasks_file_path)
        # Evaluate tasks within the input range
        if raw_data_index != -1:
            re_result = re.split(r'\s|,', raw_data_index)
            raw_data_start_index = int(re_result[0])
            raw_data_end_index = int(re_result[-1]) + 1
        else:
            raw_data_start_index = 0
            raw_data_end_index = len(file)
        print(raw_data_start_index, raw_data_end_index)

        task_range = range(raw_data_start_index, raw_data_end_index)
    elif task_mode == "single_task":
        task_range = range(0, 1)
    else:
        logger.error("task_mode error!")
        exit()

    ground_truth_data = None
    if ground_truth_mode:
        ground_truth_file_path = config['files']['Ground_Truth_File_Path']
        ground_truth_data = read_json_file(ground_truth_file_path)
        # check if ground_truth_file_path exists
        if not os.path.exists(ground_truth_file_path):
            logger.error("ground_truth_file_path not exist!")
            exit()

    for task_index in task_range:

        task_uuid = None
        if task_mode == "batch_tasks":
            task = file[task_index]
            task_name, task_uuid, reference_task_length, reference_evaluate_steps = task
            evaluate_steps = reference_evaluate_steps
            logger.info("*" * 100)
            logger.info(f"Start")
            logger.info(f"task index: {task_index}")
            logger.info(f"task name: {task_name}")
            logger.info(f"task reference length: {reference_task_length}")
            logger.info(f"raw data annotation: {reference_evaluate_steps}")
        elif task_mode == "single_task":
            task_name = single_task_name
            reference_task_length = config['steps']['Single_Task_Action_Step']
            logger.info(f"task_name: {task_name}")

        # Create HTML environment
        env = AsyncHTMLEnvironment(
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

        await run_task(mode=mode,
                       task_mode=task_mode,
                       task_name=task_name,
                       task_uuid=task_uuid,
                       config=config,
                       write_result_file_path=write_result_file_path,
                       reference_task_length=reference_task_length,
                       evaluate_steps=evaluate_steps,
                       reference_evaluate_steps=reference_evaluate_steps,
                       env=env,
                       global_reward_mode=global_reward_mode,
                       global_reward_text_model_name=global_reward_text_model_name,
                       observation_text_model_name=observation_text_model_name,
                       ground_truth_mode=ground_truth_mode,
                       ground_truth_data=ground_truth_data,
                       json_model_response=json_model_response,
                       step_stop=step_stop,
                       task_index=task_index,
                       record_time=record_time)

        await env.close()
        del env
        # if a == "q":
        #     break

    print(f"\033[31mtask finished!\033[0m")
    input(f"\033[31mPress Enter to exit...\033[0m")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the web agent in different modes.")
    parser.add_argument("--global_reward_mode",
                        choices=["dom_vision_reward",
                                 "dom_reward",
                                 "vision_reward",
                                 "no_global_reward"],
                        default="dom_reward", help="Choose the mode of global reward.")
    parser.add_argument("--index", type=str, default=-1)
    parser.add_argument("--single_task_name", type=str, default="Find Dota 2 game and add all DLC to cart in steam.")
    args = parser.parse_args()

    asyncio.run(main(global_reward_mode=args.global_reward_mode,
                     observation_text_model_name="gpt-3.5-turbo",
                     global_reward_text_model_name="gpt-3.5-turbo",
                     single_task_name=args.single_task_name,
                     raw_data_index=args.index
                     ))
