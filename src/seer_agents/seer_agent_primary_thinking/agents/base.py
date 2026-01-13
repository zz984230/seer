from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from ..models import StockAnalysisRequest
from ..knowledge_base import KnowledgeBase
from ..adk_config import adk_config
from seer.logger import logger


class ADKAgent(ABC):
    def __init__(self, agent_name: str, knowledge_base: KnowledgeBase):
        self.agent_name = agent_name
        self.knowledge_base = knowledge_base
        self.logger = logger
        self.config = adk_config
    
    @abstractmethod
    def analyze(self, request: StockAnalysisRequest, context: Dict[str, Any]) -> tuple[bool, str, Optional[Dict[str, Any]]]:
        pass
    
    def get_agent_config(self) -> Dict[str, Any]:
        return {
            "name": self.agent_name,
            "description": getattr(self, "description", ""),
            "instructions": getattr(self, "instructions", "")
        }
    
    def get_model_config(self) -> Dict[str, Any]:
        provider = self.config.model.provider
        
        if provider == "openai":
            return self.config.get_openai_config()
        elif provider == "anthropic":
            return self.config.get_anthropic_config()
        elif provider == "google":
            return self.config.get_google_config()
        else:
            return self.config.get_openai_config()
    
    def _search_knowledge(self, query: str, category: str = None, limit: int = 5) -> List:
        return self.knowledge_base.search_knowledge(query, category, limit=limit)
