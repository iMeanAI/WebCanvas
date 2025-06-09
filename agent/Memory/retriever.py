import pandas as pd
import chromadb
import os
import logging
import json
logger = logging.getLogger(__name__)

def load_qry(path):
    with open(path, 'r', encoding='utf-8') as f:
        qry_data = json.load(f)
    return qry_data

def load_cand(cand_path):
    try:
        # Read the parquet file using pandas
        cand_dict = pd.read_parquet(cand_path).to_dict()
        return cand_dict
    except Exception as e:
        logger.error(f"Error loading candidate data from {cand_path}: {str(e)}")
        raise

def get_task_workflow_description(task_id: str) -> str:
    """Get the combined workflow description of all steps for a given task ID."""
    try:
        # Load the generated steps
        with open("data/Online-Mind2Web/generated_steps/generated_task_steps.json", "r") as f:
            tasks = json.load(f)
        
        # Find the task with matching ID
        for task in tasks:
            if task["task_id"] == task_id:
                # Combine all steps into a single string
                description = f"Task: {task['confirmed_task']}\nWebsite: {task['website']}\n\nSteps:\n"
                for i, step in enumerate(task["steps"], 1):
                    description += f"{i}. Observation: {step['observation']}\n"
                    description += f"   Action: {step['action']}\n\n"
                return description
        
        return f"No workflow description found for task ID: {task_id}"
    except Exception as e:
        logger.error(f"Error getting workflow description for task {task_id}: {str(e)}")
        return f"Error retrieving workflow description: {str(e)}"
        
def build_retrieval_pool(collection_path, cand_pool):
    if not os.path.exists(collection_path):
        os.makedirs(collection_path)
    
    client = chromadb.PersistentClient(path=collection_path)
    
    # Check if collection exists
    collections = client.list_collections()
    collection_exists = any(col.name == "retrieval_pool" for col in collections)
    
    if collection_exists:
        collection = client.get_collection(name="retrieval_pool")
    else:
        # Create new collection with optimized parameters
        collection = client.create_collection(
            name="retrieval_pool",
            configuration={
                "hnsw": {
                    "space": "cosine", # Cohere models often use cosine space
                    "ef_search": 200,
                    "ef_construction": 200,
                    "max_neighbors": 32,
                    "num_threads": 4
                },
            }
        )
        # Add embeddings only for new collection
        cand_ids = list(cand_pool['annotation_id'].values())
        embeddings = list(cand_pool['embed'].values())

        collection.add(
            embeddings=embeddings,
            ids=cand_ids
        )
    
    return collection

class TestOnlyRetriever():
    def __init__(self, path):
        self.qry_pool = load_qry(path['qry_embed_path'])
        self.cand_pool = load_cand(path['cand_embed_path'])
        self.traj_pool = load_qry(path['cand_id_text_path'])
        self.collection = build_retrieval_pool(path['collection_path'], self.cand_pool)
    
    def get_task_id(self, task_name):
        for entry in self.qry_pool:
            if task_name == entry['task']:
                return entry['id']
    
    def lookup_qry_embed(self, task_name):
        for entry in self.qry_pool:
            if task_name == entry['task']:
                return entry['embedding']

    def get_cand_content(self, ids):
        retrieved_texts = []
        retrieved_image_paths = []
        for a_id in ids: 
            cand_text = self.traj_pool[a_id]['cand_text']
            cand_image_path = self.traj_pool[a_id]['cand_image_path']
            retrieved_texts.append(cand_text)
            retrieved_image_paths.append(cand_image_path)
        return retrieved_texts, retrieved_image_paths

    def get_cand_task(self, ids):
        retrieved_tasks = []
        for a_id in ids:
            # Find the index where annotation_id matches a_id
            idx = list(self.cand_pool['annotation_id'].values()).index(a_id)
            # Get the task at the same index
            cand_task = list(self.cand_pool['instruction'].values())[idx]
            retrieved_tasks.append(cand_task)
        return retrieved_tasks

    def get_task_workflow(self, ids):
        """Get workflow descriptions for the given task IDs."""
        workflow_descriptions = []
        for task_id in ids:
            description = get_task_workflow_description(task_id)
            workflow_descriptions.append(description)
        return workflow_descriptions

    def retrieve(self, task_name):
        qry_embed = self.lookup_qry_embed(task_name)
        if qry_embed is None:
            return None
            
        response = self.collection.query(
            query_embeddings=[qry_embed],
            n_results=1,
        )
        retrieved_ids = response['ids'][0]
        print(f"retrieved_ids: {retrieved_ids}")
        retrieved_texts, retrieved_image_paths = self.get_cand_content(retrieved_ids)
        retrieved_tasks = self.get_cand_task(retrieved_ids)
        retrieved_workflows = self.get_task_workflow(retrieved_ids)
        return retrieved_tasks, retrieved_texts, retrieved_image_paths, retrieved_workflows

       