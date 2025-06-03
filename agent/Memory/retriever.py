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
        
def build_retrieval_pool(collection_path, cand_pool):
    if not os.path.exists(collection_path):
        os.makedirs(collection_path)
        client = chromadb.PersistentClient(path=collection_path)
        collection = client.get_or_create_collection(name="retrieval_pool")
        cand_ids = list(cand_pool['annotation_id'].values())
        embeddings = list(cand_pool['embed'].values())

        collection.add(
            embeddings=embeddings,
            ids=cand_ids
        )
    else:
        client = chromadb.PersistentClient(path=collection_path)
        collection = client.get_or_create_collection(name="retrieval_pool")
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

    def get_cand_text(self, ids):
        retrieved_texts = []
        for a_id in ids: 
            cand_text = self.traj_pool[a_id]['cand_text']
            retrieved_texts.append(cand_text)
        return retrieved_texts

    def get_cand_task(self, ids):
        retrieved_tasks = []
        for a_id in ids:
            # Find the index where annotation_id matches a_id
            idx = list(self.cand_pool['annotation_id'].values()).index(a_id)
            # Get the task at the same index
            cand_task = list(self.cand_pool['instruction'].values())[idx]
            retrieved_tasks.append(cand_task)
        return retrieved_tasks

    def retrieve(self, task_name):
        qry_embed = self.lookup_qry_embed(task_name)
        if qry_embed is None:
            return None
            
        response = self.collection.query(
            query_embeddings=[qry_embed],
            n_results=2,
        )
        retrieved_ids = response['ids'][0]
        print(f"retrieved_ids: {retrieved_ids}")
        retrieved_texts = self.get_cand_text(retrieved_ids)
        retrieved_tasks = self.get_cand_task(retrieved_ids)
        return retrieved_tasks, retrieved_texts

       