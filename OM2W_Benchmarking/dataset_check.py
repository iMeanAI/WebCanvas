import os
import sys
from pathlib import Path

def count_trajectory_files():
    base_dir = Path("../WebCanvas/dataset")
    if not base_dir.exists():
        print(f"Error: Path '{base_dir}' does not exist")
        sys.exit(1)
        
    empty_trajectories = []
    task_count = 0
    for task_id_dir in base_dir.iterdir():
        if task_id_dir.is_dir():
            task_count += 1
            trajectory_dir = task_id_dir / "trajectory"

            if trajectory_dir.exists() and trajectory_dir.is_dir():
                files = list(trajectory_dir.iterdir())
                file_count = len(files)
                print(f"Task ID: {task_id_dir.name}, Number of Trajectory files: {file_count}")
                if file_count == 0:
                    empty_trajectories.append(task_id_dir.name)
            else:
                print(f"Task ID: {task_id_dir.name}, Trajectory folder does not exist")
                empty_trajectories.append(task_id_dir.name)
    
    print("\nThe Task ID of the empty Trajectory folder:")
    if empty_trajectories:
        for task_id in empty_trajectories:
            print(task_id)
    else:
        print("Empty trajectory folder not found")
    
    print(f"\nA total of {task_count} Task ids are processed")

if __name__ == "__main__":
    count_trajectory_files()