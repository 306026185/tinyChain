
import os
import json
import datetime

from typing import List,Union,Protocol

import ollama
import glob

import numpy as np

from tinychain.db.models import Rec,Result

def mxbai_embedding_model(prompt):
    response = ollama.embeddings(
        model='mxbai-embed-large:latest',
        prompt=prompt
    )

    return np.array(response['embedding'])


def calc_consine_similarity(embedding_one,embedding_two):
    dot_product = np.dot(embedding_one,embedding_two)

    norm_embedding_one = np.linalg.norm(embedding_one)
    norm_embedding_two = np.linalg.norm(embedding_two)

    return dot_product/(norm_embedding_one * norm_embedding_two)



embedding_dict = {
    'mxbai-embed-large:latest':mxbai_embedding_model
}

class Collection:

    def __init__(self,
                 database_name:str,
                 collection_name:str,
                 embedding_model_name:str='mxbai-embed-large:latest'
                 ) -> None:
        self.database_name = database_name
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model_name
        
        self.collection_file_path = os.path.join(self.database_name,f"{self.collection_name}.json")
        self.json_data = {}
        if os.path.exists(self.collection_file_path):
            with open(self.collection_file_path,"r") as f:
                self.json_data = json.load(f) 

    def add(self,documents:List[str],ids:List[str],namespace:str):
        
        for document,id in zip(documents,ids):
            rec = Rec(
                rec_id=id,
                document=document,
                namespace=namespace,
                create_at=str(datetime.date.today()),
                embedding="",
                is_used=True
            )

            self.add_rec(rec)

    def add_rec(self,rec:Rec):

        embedding_model = embedding_dict[self.embedding_model_name]
        embedding = embedding_model(rec.document)
        embedding_file_path = f"{self.database_name}/{self.collection_name}_{rec.namespace}_{rec.rec_id}.npy"
        np.save(embedding_file_path,embedding)
        rec.embedding = embedding_file_path
        self.json_data[rec.rec_id] = rec.model_dump()

        with open(self.collection_file_path,"w") as json_file:
            json.dump(self.json_data,json_file)


    def query_result_rank(self,result:Result):
        # result_list
        documnents = result.documents
        ids = result.ids
        distances = result.distances

        sorted_distances = distances.sort()
        print(distances)

        sorted_id = sorted(range(len(distances)), key=lambda k: distances[k], reverse=True)
        print(sorted_id)

        



    def query(self,r:Rec,n_result:int)->Result:
        if os.path.exists(self.collection_file_path):
            with open(self.collection_file_path,"r") as f:
                self.json_data = json.load(f) 

        embedding_model = embedding_dict[self.embedding_model_name]
        query_embedding = embedding_model(r.document)


        ids = []
        distances = []
        documents = []

        for rec_id,rec in self.json_data.items():
            # print(rec)
            embedding_np = np.load(rec['embedding'])
            # ids.append(rec_id)
            documents.append(rec['document'])
            distances.append(calc_consine_similarity(query_embedding,embedding_np))

        
        
        return Result(
            documents=documents,
            ids=ids,
            distances=distances
        )


class BaseDatabaseClient:

    def create_collection(self,collection_name:str):
        ...

    def is_collection_exist(self,collection_name:str):
        ...


class TinyVectorDatabaseClient:

    def __init__(self,database_name:str) -> None:
        self.database_name = database_name
        if not os.path.exists(self.database_name):
            os.makedirs(self.database_name,exist_ok=True)


    def create_collection(self,collection_name:str):
        return Collection(self.database_name,collection_name)


    