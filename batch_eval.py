"""
This is a batch test script.
This release adds the following features:
1. Support screenshots of the evaluation process
2. Support Online_Mind2Web task evaluation
3. Support access to gpt-4.1, o3-mini, o4-mini and other models

Tips: To run in a Linux environment without a visual interface, use the following command to start:
    sudo yum install -y xorg-x11-server-Xvfb
    xvfb-run -a python batch_eval.py
    
    Ubantu/Debian users can use the following command to install xvfb:
    sudo apt-get update
    sudo apt-get install -y xvfb
    xvfb-run -a python batch_eval.py
"""
#!/usr/bin/env python3
import json
import os
import subprocess
import argparse
import time
from pathlib import Path

def load_tasks(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data

def run_single_task(task, current_idx, args):
    task_name = task["confirmed_task"]
    website = task.get("website", "about:blank")
    
    command = [
        "python", "eval.py",
        "--global_reward_mode", args.global_reward_mode,
        "--index", str(current_idx),
        "--single_task_name", task_name,
        "--single_task_website", website,
        "--snapshot", args.snapshot,
        "--planning_text_model", args.planning_text_model,
        "--global_reward_text_model", args.global_reward_text_model
    ]
    
    print(f"\n{'='*80}")
    print(f"Task [{current_idx}]: {task_name}")
    print(f"Website: {website}")
    print(f"{'='*80}")
    
    try:
        subprocess.run(command, check=True)
        print(f"Mission accomplished: {task_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Task failure: {task_name}")
        print(f"Error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Online-Mind2Web Task')
    parser.add_argument('--json_path', type=str, default='data/Online-Mind2Web/72exp30.json',
                        help='JSON task file path')
    parser.add_argument('--global_reward_mode', type=str, default='dom_reward',
                        help='Global Reward Mode: dom_reward/no_global_reward/dom_vision_reward')
    parser.add_argument('--index', type=int, default=-1,
                        help='Task index')
    parser.add_argument('--snapshot', type=str, default='results_new/exp',
                        help='Snapshot directory')
    parser.add_argument('--planning_text_model', type=str, default='gpt-4.1',
                        help='planning_text_model: gpt-4.1/gpt-4o-2024-08-06')
    parser.add_argument('--global_reward_text_model', type=str, default='gpt-4.1',
                        help='global_reward_text_model: gpt-4.1/gpt-4o-2024-08-06')
    parser.add_argument('--start_idx', type=int, default=0,
                        help='The index to start the task')
    parser.add_argument('--end_idx', type=int, default=None,
                        help='The index of the finished task (excluding)')
    parser.add_argument('--delay', type=int, default=5,
                        help='Latency between tasks (seconds)')
    parser.add_argument('--output_log', type=str, default='results_new/exp/batch_run_log.txt',
                        help='output_log')
    
    args = parser.parse_args()
    
    # Loading tasks
    json_path = Path(args.json_path)
    if not json_path.exists():
        print(f"Error: File does not exist - {json_path}")
        return
    
    tasks = load_tasks(json_path)
    start_idx = args.start_idx
    end_idx = args.end_idx if args.end_idx is not None else len(tasks)
    
    total_tasks = end_idx - start_idx
    successful_tasks = 0
    
    with open(args.output_log, 'w') as log_file:
        log_file.write(f"The batch job run starts: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"total_tasks: {total_tasks}\n\n")
    
    # Run the selected task
    for i, task_data in enumerate(tasks[start_idx:end_idx]):
        current_idx = start_idx + i
        task_name = task_data["confirmed_task"]
        website = task_data.get("website", "about:blank")

        with open(args.output_log, 'a') as log_file:
            # log_file.write(f"[{current_idx}/{len(tasks)}] Running tasks: {task}\n")
            log_file.write(f"[{current_idx}/{len(tasks)}] Running task: {task_name}\n")
            log_file.write(f"Website: {website}\n")
        
        success = run_single_task(task_data, current_idx, args)
        if success:
            successful_tasks += 1
        
        # Logging results
        with open(args.output_log, 'a') as log_file:
            log_file.write(f"results: {'Success' if success else 'failure'}\n\n")
        if i < total_tasks - 1:
            print(f"waiting {args.delay} continue to the next task after seconds...")
            time.sleep(args.delay)
    
    with open(args.output_log, 'a') as log_file:
        log_file.write(f"\nFinish: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"Total_tasks: {total_tasks}\n")
        log_file.write(f"Number of successful tasks: {successful_tasks}\n")
        log_file.write(f"Success rate: {successful_tasks/total_tasks*100:.2f}%\n")
    
    print(f"\n{'='*80}")
    print(f"Total_tasks: {total_tasks}")
    print(f"Number of successful tasks: {successful_tasks}")
    print(f"Success rate: {successful_tasks/total_tasks*100:.2f}%")
    print(f"save: {args.output_log}")

if __name__ == "__main__":
    main()
    