import os
import json
import time
from datetime import datetime

class RAGLogger:
    """Utility classes that record the retrieval process and results of RAG"""
    
    def __init__(self):
        self.rag_dir = os.path.join("rag_result", "rag_json")
        os.makedirs(self.rag_dir, exist_ok=True)
        
    def log_rag_step(self, task_id, step_idx, rag_data):
        """
        The information of a RAG decision step is recorded

        Args:
        task_id: Task ID or task name
        step_idx: The index of the current step
        rag_data: A dictionary containing information about RAGs
        """
        safe_task_id = self._get_safe_filename(str(task_id))
        filename = f"{safe_task_id}.json"
        filepath = os.path.join(self.rag_dir, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
        else:
            task_data = {
                "task_id": task_id,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "steps": []
            }
        
        # add or update the step
        if step_idx < len(task_data["steps"]):
            task_data["steps"][step_idx].update(rag_data)
        else:
            while len(task_data["steps"]) < step_idx:
                task_data["steps"].append({"step_idx": len(task_data["steps"]), "empty": True})
            
            rag_data["step_idx"] = step_idx
            rag_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            task_data["steps"].append(rag_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(task_data, f, ensure_ascii=False, indent=2)
            
        return filepath
    
    def _get_safe_filename(self, filename):
        """Converts the string to a secure filename"""
        for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|', ' ']:
            filename = filename.replace(char, '_')
        return filename