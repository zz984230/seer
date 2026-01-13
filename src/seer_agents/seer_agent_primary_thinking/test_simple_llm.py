from google.adk.agents import LlmAgent
from google.genai import types
from seer.logger import logger


def test_simple_llm_agent():
    logger.info("=" * 60)
    logger.info("测试: 简单 LlmAgent 调用")
    logger.info("=" * 60)
    
    try:
        agent = LlmAgent(
            name="test_agent",
            model="Qwen/Qwen3-235B-A22B-Instruct-2507",
            instruction="你是一个专业的股票分析专家，请回答用户的问题。",
            generate_content_config=types.GenerateContentConfig(
                temperature=0.7,
                maxOutputTokens=1000
            )
        )
        
        logger.info("✓ LlmAgent 初始化成功")
        
        # 测试调用
        from google.adk.agents.invocation_context import InvocationContext
        
        ctx = InvocationContext(
            invocation_id="test_invocation",
            user_id="test_user",
            session_id="test_session",
            app_name="test_app"
        )
        
        logger.info("✓ InvocationContext 创建成功")
        
        # 尝试异步运行
        import asyncio
        
        async def run_agent():
            try:
                events = []
                async for event in agent.run_async(ctx):
                    events.append(event)
                    logger.info(f"收到事件: {type(event).__name__}")
                return events
            except Exception as e:
                logger.error(f"运行Agent失败: {str(e)}")
                import traceback
                traceback.print_exc()
                return None
        
        result = asyncio.run(run_agent())
        
        if result:
            logger.info(f"✓ Agent 运行成功，收到 {len(result)} 个事件")
            return True
        else:
            logger.warning("✗ Agent 运行失败")
            return False
            
    except Exception as e:
        logger.error(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_simple_llm_agent()