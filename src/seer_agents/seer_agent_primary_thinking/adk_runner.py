"""
简化的 Google ADK Runner 包装器
用于在项目中使用 Google ADK 的 LlmAgent
"""
import asyncio
import threading
from typing import Optional, Any, AsyncGenerator
from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.sessions.session import Session
from seer.logger import logger


class SimpleADKRunner:
    """简化的 ADK Runner 包装器"""
    
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.memory_service = InMemoryMemoryService()
        self.artifact_service = InMemoryArtifactService()
        self.runners = {}
        self.lock = asyncio.Lock()
    
    async def _get_or_create_runner(self, agent: LlmAgent, app_name: str = "seer_stock_analysis") -> Runner:
        """获取或创建 Runner"""
        async with self.lock:
            if agent.name not in self.runners:
                runner = Runner(
                    app_name=app_name,
                    agent=agent,
                    session_service=self.session_service,
                    memory_service=self.memory_service,
                    artifact_service=self.artifact_service
                )
                self.runners[agent.name] = runner
                logger.info(f"创建 Runner: {agent.name}")
            
            return self.runners[agent.name]
    
    async def run_agent(
        self,
        agent: LlmAgent,
        user_message: str,
        user_id: str = "default_user",
        session_id: str = "default_session",
        app_name: str = "seer_stock_analysis"
    ) -> str:
        """
        运行 Agent 并返回文本响应
        
        Args:
            agent: LlmAgent 实例
            user_message: 用户消息
            user_id: 用户ID
            session_id: 会话ID
            app_name: 应用名称
            
        Returns:
            Agent 的文本响应
        """
        try:
            runner = await self._get_or_create_runner(agent, app_name)
            
            new_message = types.Content(
                role="user",
                parts=[types.Part(text=user_message)]
            )
            
            response_text = ""
            
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=new_message
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text += part.text
            
            return response_text
            
        except Exception as e:
            logger.error(f"运行 Agent 失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return ""
    
    def run_agent_sync(
        self,
        agent: LlmAgent,
        user_message: str,
        user_id: str = "default_user",
        session_id: str = "default_session",
        app_name: str = "seer_stock_analysis"
    ) -> str:
        """
        同步运行 Agent
        
        Args:
            agent: LlmAgent 实例
            user_message: 用户消息
            user_id: 用户ID
            session_id: 会话ID
            app_name: 应用名称
            
        Returns:
            Agent 的文本响应
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.run_agent(agent, user_message, user_id, session_id, app_name)
        )


# 全局单例
_adk_runner = None
_runner_lock = threading.Lock()


def get_adk_runner() -> SimpleADKRunner:
    """获取全局 ADK Runner 单例"""
    global _adk_runner
    
    if _adk_runner is None:
        with _runner_lock:
            if _adk_runner is None:
                _adk_runner = SimpleADKRunner()
                logger.info("初始化全局 ADK Runner")
    
    return _adk_runner