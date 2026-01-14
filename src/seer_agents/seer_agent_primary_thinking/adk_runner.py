"""
简化的 Google ADK Runner 包装器
用于在项目中使用 Google ADK 的 LiteLlm
"""
import threading
from typing import Optional, Any
from google.genai import types
from google.adk.models.lite_llm import LiteLlm, LlmRequest
from seer.logger import logger


class SimpleADKRunner:
    """简化的 ADK Runner 包装器"""
    
    def __init__(self):
        pass
    
    async def run_agent(
        self,
        agent: LiteLlm,
        user_message: str,
        user_id: str = "default_user",
        session_id: str = "default_session",
        app_name: str = "seer_stock_analysis"
    ) -> str:
        """
        运行 Agent 并返回文本响应
        
        Args:
            agent: LiteLlm 实例
            user_message: 用户消息
            user_id: 用户ID
            session_id: 会话ID (LiteLlm 不使用)
            app_name: 应用名称
            
        Returns:
            Agent 的文本响应
        """
        try:
            new_message = types.Content(
                role="user",
                parts=[types.Part(text=user_message)]
            )
            
            llm_request = LlmRequest(contents=[new_message])
            
            response_text = ""
            
            async for event in agent.generate_content_async(llm_request):
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
        agent: LiteLlm,
        user_message: str,
        user_id: str = "default_user",
        session_id: str = "default_session",
        app_name: str = "seer_stock_analysis"
    ) -> str:
        """
        同步运行 Agent
        
        Args:
            agent: LiteLlm 实例
            user_message: 用户消息
            user_id: 用户ID
            session_id: 会话ID (LiteLlm 不使用)
            app_name: 应用名称
            
        Returns:
            Agent 的文本响应
        """
        import asyncio
        
        async def run():
            return await self.run_agent(agent, user_message, user_id, session_id, app_name)
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(run())


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