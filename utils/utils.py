import json
import os

def load_json(file_path):
    """Load JSON data from a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load JSON file {file_path}: {e}")
        return {}

def save_json(file_path, data):
    try:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"The results have been saved to {file_path}")
    except Exception as e:
        print(f"Failed to save the JSON file {file_path}: {e}")