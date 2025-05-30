import json
import os
from collections import defaultdict, Counter

def process_results_file(results_file, task_id_to_level):
    evaluation_results = []
    with open(results_file, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    result = json.loads(line)
                    evaluation_results.append(result)
                except json.JSONDecodeError:
                    print(f"Unable to parse JSON lines: {line[:50]}...")

    # Success/failure by difficulty
    level_stats = defaultdict(lambda: {"total": 0, "success": 0})
    total_stats = {"total": 0, "success": 0}
    unknown_level_tasks = []

    for result in evaluation_results:
        task_id = result.get("task_id")
        if not task_id:
            print("Missing results for task_id")
            continue
            
        predicted_label = result.get("predicted_label")
        if predicted_label is None:
            print(f"task {task_id} loss predicted_label")
            continue
            
        level = task_id_to_level.get(task_id)
        if not level:
            unknown_level_tasks.append(task_id)
            continue
            
        level_stats[level]["total"] += 1
        level_stats[level]["success"] += predicted_label
        
        total_stats["total"] += 1
        total_stats["success"] += predicted_label
    
    return {
        "total_stats": total_stats,
        "level_stats": level_stats,
        "unknown_level_tasks": unknown_level_tasks
    }

def print_statistics(stats, file_name):
    total_stats = stats["total_stats"]
    level_stats = stats["level_stats"]
    unknown_level_tasks = stats["unknown_level_tasks"]
    
    print(f"\n{file_name} Evaluation results Statistics:")
    print("-" * 50)
    print(f"Total number of evaluation tasks: {total_stats['total']}")
    
    if total_stats["total"] > 0:
        print(f"Total success rate: {total_stats['success']/total_stats['total']*100:.2f}%")
    else:
        print("No data")
        
    print("-" * 50)
    print("Statistics by difficulty Level:")
    for level in ["easy", "medium", "hard"]:
        stats = level_stats.get(level, {"total": 0, "success": 0})
        if stats["total"] > 0:
            success_rate = stats["success"] / stats["total"] * 100
            print(f"{level.capitalize()} task: {stats['success']}/{stats['total']} Success rate: {success_rate:.2f}%")
        else:
            print(f"{level.capitalize()} task: no data")
    
    if unknown_level_tasks:
        print("-" * 50)
        print(f"{len(unknown_level_tasks)} the difficulty level was not found")
        print(f"Examples of task ids with unknown difficulty levels: {unknown_level_tasks[:3]}")

def calculate_success_rates():
    with open("../WebCanvas/data/Online-Mind2Web/Online_Mind2Web.json", "r") as f:
        task_levels = json.load(f)

    task_id_to_level = {task["task_id"]: task["level"] for task in task_levels}
    
    # define the result files to process
    results_files = [
        "../WebCanvas/results/WebJudge_Online_Mind2Web_eval_gpt-4o_score_threshold_3_auto_eval_results.json"
        ]
    
    for results_file in results_files:
        if not os.path.exists(results_file):
            print(f"Warning: The {results_file} does not exist, skip")
            continue
            
        stats = process_results_file(results_file, task_id_to_level)
        print_statistics(stats, os.path.basename(results_file))

if __name__ == "__main__":
    calculate_success_rates()