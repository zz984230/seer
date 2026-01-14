from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()


class ADKModelConfig(BaseModel):
    provider: str = Field(default="openai", description="模型提供商")
    name: str = Field(default="gpt-4o", description="模型名称")
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: int = Field(default=4096, description="最大token数")


class ADKAgentConfig(BaseModel):
    name: str = Field(default="primary_thinking_agent", description="Agent名称")
    description: str = Field(default="", description="Agent描述")
    instructions: str = Field(default="", description="Agent指令")
    sub_agents: List[str] = Field(default_factory=list, description="子Agent列表")


class ADKConfig(BaseSettings):
    model: ADKModelConfig = Field(default_factory=ADKModelConfig)
    agent: ADKAgentConfig = Field(default_factory=ADKAgentConfig)
    
    adk_model_provider: Optional[str] = Field(default=None, alias="ADK_MODEL_PROVIDER")
    adk_model_name: Optional[str] = Field(default=None, alias="ADK_MODEL_NAME")
    adk_model_temperature: Optional[float] = Field(default=None, alias="ADK_MODEL_TEMPERATURE")
    adk_model_max_tokens: Optional[int] = Field(default=None, alias="ADK_MODEL_MAX_TOKENS")
    
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_api_base: Optional[str] = Field(default="https://api.openai.com/v1", alias="OPENAI_API_BASE")
    
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_collection_name: str = Field(default="seer_knowledge", alias="QDRANT_COLLECTION_NAME")
    qdrant_vector_size: int = Field(default=1536, alias="QDRANT_VECTOR_SIZE")
    qdrant_use_memory: bool = Field(default=True, alias="QDRANT_USE_MEMORY")
    qdrant_cache_dir: str = Field(default="d:/code/seer/data/primary_thinking/vector", alias="QDRANT_CACHE_DIR")
    
    embedding_model_provider: str = Field(default="openai", alias="EMBEDDING_MODEL_PROVIDER")
    embedding_model_name: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL_NAME")
    embedding_model_api_key: Optional[str] = Field(default=None, alias="EMBEDDING_MODEL_API_KEY")
    embedding_model_base_url: Optional[str] = Field(default="https://api.openai.com/v1", alias="EMBEDDING_MODEL_BASE_URL")
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )
    
    def get_openai_config(self) -> Dict[str, Any]:
        return {
            "api_key": self.openai_api_key,
            "base_url": self.openai_api_base,
            "model": self.model.name,
            "temperature": self.model.temperature,
            "max_tokens": self.model.max_tokens
        }
    
    def get_anthropic_config(self) -> Dict[str, Any]:
        return {
            "api_key": self.anthropic_api_key,
            "model": self.model.name,
            "temperature": self.model.temperature,
            "max_tokens": self.model.max_tokens
        }
    
    def get_google_config(self) -> Dict[str, Any]:
        return {
            "api_key": self.google_api_key,
            "model": self.model.name,
            "temperature": self.model.temperature,
            "max_tokens": self.model.max_tokens
        }
    
    def get_agent_config(self) -> Dict[str, Any]:
        return {
            "name": self.agent.name,
            "description": self.agent.description,
            "instructions": self.agent.instructions
        }
    
    def get_llm_agent_config(self, agent_name: str, instructions: str) -> Dict[str, Any]:
        from google.genai import types
        
        return {
            "name": agent_name,
            "model": self.model.name,
            "instruction": instructions,
            "generate_content_config": types.GenerateContentConfig(
                temperature=self.model.temperature,
                maxOutputTokens=self.model.max_tokens
            )
        }
    
    def get_model_config(self) -> Dict[str, Any]:
        provider = self.model.provider
        
        if provider == "openai":
            return self.get_openai_config()
        elif provider == "anthropic":
            return self.get_anthropic_config()
        elif provider == "google":
            return self.get_google_config()
        else:
            return self.get_openai_config()
    
    def get_qdrant_config(self) -> Dict[str, Any]:
        return {
            "url": self.qdrant_url,
            "collection_name": self.qdrant_collection_name,
            "vector_size": self.qdrant_vector_size,
            "use_memory": self.qdrant_use_memory,
            "cache_dir": self.qdrant_cache_dir
        }
    
    def get_embedding_model_config(self) -> Dict[str, Any]:
        return {
            "api_key": self.embedding_model_api_key,
            "base_url": self.embedding_model_base_url,
            "model": self.embedding_model_name
        }
    
    def model_post_init(self, __context: Any) -> None:
        if self.adk_model_provider:
            self.model.provider = self.adk_model_provider
        if self.adk_model_name:
            self.model.name = self.adk_model_name
        if self.adk_model_temperature:
            self.model.temperature = self.adk_model_temperature
        if self.adk_model_max_tokens:
            self.model.max_tokens = self.adk_model_max_tokens


adk_config = ADKConfig()
adk_config.model_post_init(None)
