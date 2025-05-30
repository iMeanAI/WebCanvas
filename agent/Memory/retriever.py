import pandas as pd
import chromadb
import os
import logging
import json
logger = logging.getLogger(__name__)

def load_qry(qry_path):
    qry_data = []
    with open (qry_path, 'r') as f:
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
    return collection

class TestOnlyRetriever():
    def __init__(self, path):
        self.qry_pool = load_qry(path['qry_embed_path'])
        self.cand_pool = load_cand(path['cand_embed_path'])
        self.collection = build_retrieval_pool(path['collection_path'], self.cand_pool)
    
    def get_task_id(self, task_name):
        for entry in self.qry_pool:
            if task_name == entry['task']:
                return entry['id']
    
    def lookup_qry_embed(self, task_name):
        for entry in self.qry_pool:
            if task_name == entry['task']:
                return entry['embedding']

    def retrieve(self, task_name):
        qry_embed = self.lookup_qry_embed(task_name)
        if qry_embed is None:
            return None
            
        response = self.collection.query(
            query_embeddings=[qry_embed],
            n_results=1,
        )
        retrieved_ids = response['ids'][0]
        
        return retrieved_ids

       