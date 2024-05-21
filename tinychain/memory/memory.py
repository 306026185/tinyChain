from abc import ABC,abstractmethod

from typing import Tuple,List
from data_type import RecordMessage

class CoreMemory:
    def __init__(self, 
                 persona=None, 
                 human=None, 
                 persona_char_limit=None, 
                 human_char_limit=None,
                 archival_memory_exists=True) -> None:
        
        self.persona = persona
        self.human = human
        self.persona_char_limit = persona_char_limit
        self.human_char_limit = human_char_limit

        # affects the error message the AI will see on overflow inserts
        self.archival_memory_exists = archival_memory_exists

    def __repr__(self) -> str:
        return f"\n### CORE MEMORY ###" + f"\n=== Persona ===\n{self.persona}" + f"\n\n=== Human ===\n{self.human}"
    

    def to_dict(self):
        return {
            "persona": self.persona,
            "human": self.human,
        }
    
    def edit_persona(self, new_persona):
        if self.persona_char_limit and len(new_persona) > self.persona_char_limit:
            error_msg = f"Edit failed: Exceeds {self.persona_char_limit} character limit (requested {len(new_persona)})."
            if self.archival_memory_exists:
                error_msg = f"{error_msg} Consider summarizing existing core memories in 'persona' and/or moving lower priority content to archival memory to free up space in core memory, then trying again."
            raise ValueError(error_msg)

        self.persona = new_persona
        return len(self.persona)

    def edit_human(self, new_human):
        if self.human_char_limit and len(new_human) > self.human_char_limit:
            error_msg = f"Edit failed: Exceeds {self.human_char_limit} character limit (requested {len(new_human)})."
            if self.archival_memory_exists:
                error_msg = f"{error_msg} Consider summarizing existing core memories in 'human' and/or moving lower priority content to archival memory to free up space in core memory, then trying again."
            raise ValueError(error_msg)

        self.human = new_human
        return len(self.human)
    
    def edit_append(self, field, content, sep="\n"):
        if field == "persona":
            new_content = self.persona + sep + content
            return self.edit_persona(new_content)
        elif field == "human":
            new_content = self.human + sep + content
            return self.edit_human(new_content)
        else:
            raise KeyError(f'No memory section named {field} (must be either "persona" or "human")')
        
    def edit_replace(self, field, old_content, new_content):
        if len(old_content) == 0:
            raise ValueError("old_content cannot be an empty string (must specify old_content to replace)")

        if field == "persona":
            if old_content in self.persona:
                new_persona = self.persona.replace(old_content, new_content)
                return self.edit_persona(new_persona)
            else:
                raise ValueError("Content not found in persona (make sure to use exact string)")
        elif field == "human":
            if old_content in self.human:
                new_human = self.human.replace(old_content, new_content)
                return self.edit_human(new_human)
            else:
                raise ValueError("Content not found in human (make sure to use exact string)")
        else:
            raise KeyError(f'No memory section named {field} (must be either "persona" or "human")')
        
class ArchivalMemory(ABC):
    @abstractmethod
    def insert(self, memory_string: str):
        """Insert new archival memory

        :param memory_string: Memory string to insert
        :type memory_string: str
        """

    @abstractmethod
    def search(self, query_string, count=None, start=None) -> Tuple[List[str], int]:
        """Search archival memory

        :param query_string: Query string
        :type query_string: str
        :param count: Number of results to return (None for all)
        :type count: Optional[int]
        :param start: Offset to start returning results from (None if 0)
        :type start: Optional[int]

        :return: Tuple of (list of results, total number of results)
        """

    @abstractmethod
    def __repr__(self) -> str:
        pass

class RecallMemory(ABC):
    @abstractmethod
    def text_search(self, query_string, count=None, start=None):
        """Search messages that match query_string in recall memory"""

    @abstractmethod
    def date_search(self, start_date, end_date, count=None, start=None):
        """Search messages between start_date and end_date in recall memory"""

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def insert(self, message: RecordMessage):
        """Insert message into recall memory"""

class BaseRecallMemory(RecallMemory):
    """Recall memory based on base functions implemented by storage connectors"""

    def __init__(self, agent_state, restrict_search_to_summaries=False):
        # If true, the pool of messages that can be queried are the automated summaries only
        # (generated when the conversation window needs to be shortened)
        self.restrict_search_to_summaries = restrict_search_to_summaries
        from memgpt.agent_store.storage import StorageConnector

        self.agent_state = agent_state

        # create embedding model
        self.embed_model = embedding_model(agent_state.embedding_config)
        self.embedding_chunk_size = agent_state.embedding_config.embedding_chunk_size

        # create storage backend
        self.storage = StorageConnector.get_recall_storage_connector(user_id=agent_state.user_id, agent_id=agent_state.id)
        # TODO: have some mechanism for cleanup otherwise will lead to OOM
        self.cache = {}

    def get_all(self, start=0, count=None):
        results = self.storage.get_all(start, count)
        results_json = [message.to_openai_dict() for message in results]
        return results_json, len(results)

    def text_search(self, query_string, count=None, start=None):
        results = self.storage.query_text(query_string, count, start)
        results_json = [message.to_openai_dict_search_results() for message in results]
        return results_json, len(results)

    def date_search(self, start_date, end_date, count=None, start=None):
        results = self.storage.query_date(start_date, end_date, count, start)
        results_json = [message.to_openai_dict_search_results() for message in results]
        return results_json, len(results)

    def __repr__(self) -> str:
        total = self.storage.size()
        system_count = self.storage.size(filters={"role": "system"})
        user_count = self.storage.size(filters={"role": "user"})
        assistant_count = self.storage.size(filters={"role": "assistant"})
        function_count = self.storage.size(filters={"role": "function"})
        other_count = total - (system_count + user_count + assistant_count + function_count)

        memory_str = (
            f"Statistics:"
            + f"\n{total} total messages"
            + f"\n{system_count} system"
            + f"\n{user_count} user"
            + f"\n{assistant_count} assistant"
            + f"\n{function_count} function"
            + f"\n{other_count} other"
        )
        return f"\n### RECALL MEMORY ###" + f"\n{memory_str}"

    def insert(self, message: RecordMessage):
        self.storage.insert(message)

    def insert_many(self, messages: List[RecordMessage]):
        self.storage.insert_many(messages)

    def save(self):
        self.storage.save()

    def __len__(self):
        return self.storage.size()