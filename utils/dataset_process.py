import os
import json
import shutil
from pathlib import Path
import re

def normalize_filename(name):
    # Replace common illegal characters
    replacements = {
        '/': '_', 
        '\\': '_',
        ':': '_',
        '*': '',
        '?': '',
        '"': '',
        '<': '',
        '>': '',
        '|': '_'
    }
    for char, replacement in replacements.items():
        name = name.replace(char, replacement)
    return name

def find_best_match(folder_name, task_map):
    """Task of finding the best match"""
    # Direct matching
    if folder_name in task_map:
        return task_map[folder_name]
    
    # Attempt to normalize matches
    normalized_folder = normalize_filename(folder_name)
    for task_name, task_id in task_map.items():
        if normalize_filename(task_name) == normalized_folder:
            return task_id
    
    # Try a partial match
    for task_name, task_id in task_map.items():
        if task_name.startswith(folder_name) or folder_name in task_name:
            return task_id
    
    return None

def process_dataset():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    screenshots_dir = os.path.join(base_dir, "results_new/exp", "img_screenshots")
    json_results_dir = os.path.join(base_dir, "results_new/exp", "json")
    output_dir = os.path.join(base_dir, "dataset_new/exp")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # task
    with open(os.path.join(base_dir, "data/Online-Mind2Web/Online_Mind2Web.json"), "r") as f:
        tasks = json.load(f)
    # with open(os.path.join(base_dir, "data/Online-Mind2Web/hard_task.json"), "r") as f:
    #     tasks = json.load(f)
        
    # Create a task_id to confirmed_task mapping and reverse
    task_map = {}
    id_map = {}
    for task in tasks:
        if "confirmed_task" in task and "task_id" in task:
            task_map[task["confirmed_task"]] = task["task_id"]
            id_map[task["task_id"]] = task["confirmed_task"]
    
    available_json_files = set(f for f in os.listdir(json_results_dir) if f.endswith('.json'))
    processed_count = 0
    failed_folders = []
    
    for folder_name in os.listdir(screenshots_dir):
        folder_path = os.path.join(screenshots_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue
        
        task_id = find_best_match(folder_name, task_map)
        
        if not task_id:
            print(f"Warning: No match for task ID found '{folder_name}'")
            failed_folders.append(folder_name)
            continue
        task_dir = os.path.join(output_dir, task_id)
        trajectory_dir = os.path.join(task_dir, "trajectory")
        os.makedirs(trajectory_dir, exist_ok=True)

        all_images = []
        def collect_images(directory, relative_path=""):
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    collect_images(item_path, os.path.join(relative_path, item))
                elif item.lower().endswith(('.png', '.jpg', '.jpeg')):
                    all_images.append({
                        'full_path': item_path,
                        'relative_path': os.path.join(relative_path, item),
                        'filename': item
                    })

        collect_images(folder_path)

        all_images.sort(key=lambda x: int(re.findall(r'\d+', x['filename'])[0]) if re.findall(r'\d+', x['filename']) else 0)
        # copy images to the trajectory directory
        for i, img_info in enumerate(all_images):
            file_number = re.findall(r'\d+', img_info['filename'])
            file_number = file_number[0] if file_number else str(i)
            file_ext = os.path.splitext(img_info['filename'])[1]
            
            new_filename = f"step_{file_number}_screenshot{file_ext}"
            dst = os.path.join(trajectory_dir, new_filename)
            
            shutil.copy2(img_info['full_path'], dst)
            
            print(f"copy: {img_info['relative_path']} -> {new_filename}")
        
        json_filename = f"{task_id}.json"
        if json_filename in available_json_files:
            src = os.path.join(json_results_dir, json_filename)
            dst = os.path.join(task_dir, "result.json")
            shutil.copy2(src, dst)
            processed_count += 1
            print(f"ok: '{folder_name}' -> {json_filename} (task: {id_map.get(task_id, 'unknown')})")
        else:
            print(f"Warning: Result file for task not found '{folder_name}' (task_id: {task_id})")
    
    print(f"Successfully processed {processed_count} tasks")
    
    if failed_folders:
        print("\nNo task ID was found for the following folders")
        for folder in failed_folders:
            print(f"  - {folder}")

if __name__ == "__main__":
    process_dataset()
    print("ok!")