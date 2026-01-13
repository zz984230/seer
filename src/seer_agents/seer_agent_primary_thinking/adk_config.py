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
    
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_api_base: Optional[str] = Field(default="https://api.openai.com/v1", alias="OPENAI_API_BASE")
    
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    
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


adk_config = ADKConfig()
