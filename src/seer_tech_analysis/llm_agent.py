from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import json
from .models import LLMConfig, AgentAnalysis
from .config import settings
from seer.logger import logger


class LLMProvider(ABC):
    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logger
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        pass
    
    @abstractmethod
    def chat_with_functions(self, messages: List[Dict[str, str]], functions: List[Dict[str, Any]], **kwargs) -> str:
        pass


class OpenAIProvider(LLMProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=config.api_key,
                base_url=config.base_url,
                timeout=config.timeout
            )
            self.logger.info("OpenAI客户端初始化成功")
        except ImportError:
            self.logger.error("未安装openai库，请运行: pip install openai")
            raise
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"OpenAI调用失败: {str(e)}")
            raise
    
    def chat_with_functions(self, messages: List[Dict[str, str]], functions: List[Dict[str, Any]], **kwargs) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                functions=functions,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"OpenAI函数调用失败: {str(e)}")
            raise


class AnthropicProvider(LLMProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            from anthropic import Anthropic
            self.client = Anthropic(
                api_key=config.api_key,
                timeout=config.timeout
            )
            self.logger.info("Anthropic客户端初始化成功")
        except ImportError:
            self.logger.error("未安装anthropic库，请运行: pip install anthropic")
            raise
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            system_message = ""
            user_messages = []
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    user_messages.append(msg)
            
            response = self.client.messages.create(
                model=self.config.model_name,
                system=system_message,
                messages=user_messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                **kwargs
            )
            return response.content[0].text
        except Exception as e:
            self.logger.error(f"Anthropic调用失败: {str(e)}")
            raise
    
    def chat_with_functions(self, messages: List[Dict[str, str]], functions: List[Dict[str, Any]], **kwargs) -> str:
        return self.chat(messages, **kwargs)


class GoogleProvider(LLMProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.api_key)
            self.model = genai.GenerativeModel(config.model_name)
            self.logger.info("Google客户端初始化成功")
        except ImportError:
            self.logger.error("未安装google-generativeai库，请运行: pip install google-generativeai")
            raise
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': self.config.temperature,
                    'max_output_tokens': self.config.max_tokens
                }
            )
            return response.text
        except Exception as e:
            self.logger.error(f"Google调用失败: {str(e)}")
            raise
    
    def chat_with_functions(self, messages: List[Dict[str, str]], functions: List[Dict[str, Any]], **kwargs) -> str:
        return self.chat(messages, **kwargs)


class LLMFactory:
    @staticmethod
    def create_provider(config: LLMConfig) -> LLMProvider:
        provider_map = {
            'openai': OpenAIProvider,
            'anthropic': AnthropicProvider,
            'google': GoogleProvider
        }
        
        provider_class = provider_map.get(config.provider.lower())
        if not provider_class:
            raise ValueError(f"不支持的LLM提供商: {config.provider}")
        
        return provider_class(config)


class LLMAgent:
    def __init__(self, agent_name: str, agent_type: str, config: Optional[LLMConfig] = None):
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.config = config or settings.llm
        self.provider = LLMFactory.create_provider(self.config)
        self.logger = logger
    
    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        base_prompt = f"""你是一个专业的股票技术分析专家，专注于{self.agent_type}分析。
你的任务是基于提供的技术数据，给出专业的分析建议。

分析要求：
1. 基于数据给出客观、专业的分析
2. 提供明确的买入/卖出/持有建议
3. 给出置信度评分（0-1之间）
4. 评估风险等级（低/中/高）
5. 提供详细的推理过程

输出格式要求：
- 建议：买入/卖出/持有
- 置信度：0.XX
- 风险等级：低/中/高
- 推理过程：详细说明分析逻辑
"""
        
        if self.agent_type == "technical":
            base_prompt += """
技术指标分析要点：
- MACD：关注金叉死叉、柱状图变化
- RSI：关注超买超卖区域、背离信号
- KDJ：关注KDJ三线位置和交叉
- 均线：关注多头空头排列、支撑压力
"""
        elif self.agent_type == "pattern":
            base_prompt += """
形态识别分析要点：
- 头肩顶/底：关注颈线突破
- 双顶/双底：关注颈线突破
- 三角形：关注突破方向
- 楔形：关注突破方向
"""
        elif self.agent_type == "volume":
            base_prompt += """
量价关系分析要点：
- 量增价涨：多头力量强劲
- 量增价跌：恐慌性抛售
- 量减价涨：上涨动力不足
- 量减价跌：下跌动力不足
"""
        
        return base_prompt
    
    def _build_user_prompt(self, context: Dict[str, Any]) -> str:
        prompt_parts = []
        
        if 'stock_code' in context:
            prompt_parts.append(f"股票代码: {context['stock_code']}")
        if 'stock_name' in context:
            prompt_parts.append(f"股票名称: {context['stock_name']}")
        if 'analysis_date' in context:
            prompt_parts.append(f"分析日期: {context['analysis_date']}")
        
        prompt_parts.append("\n技术数据:")
        
        if 'technical_indicators' in context:
            indicators = context['technical_indicators']
            if 'macd' in indicators:
                macd = indicators['macd']
                prompt_parts.append(f"\nMACD:")
                prompt_parts.append(f"- DIF: {macd.dif[-1]:.4f}")
                prompt_parts.append(f"- DEA: {macd.dea[-1]:.4f}")
                prompt_parts.append(f"- MACD: {macd.macd[-1]:.4f}")
                prompt_parts.append(f"- 描述: {macd.description}")
            
            if 'rsi' in indicators:
                rsi = indicators['rsi']
                prompt_parts.append(f"\nRSI:")
                prompt_parts.append(f"- RSI6: {rsi.rsi6[-1]:.2f}")
                prompt_parts.append(f"- RSI12: {rsi.rsi12[-1]:.2f}")
                prompt_parts.append(f"- RSI24: {rsi.rsi24[-1]:.2f}")
                prompt_parts.append(f"- 描述: {rsi.description}")
            
            if 'kdj' in indicators:
                kdj = indicators['kdj']
                prompt_parts.append(f"\nKDJ:")
                prompt_parts.append(f"- K: {kdj.k[-1]:.2f}")
                prompt_parts.append(f"- D: {kdj.d[-1]:.2f}")
                prompt_parts.append(f"- J: {kdj.j[-1]:.2f}")
                prompt_parts.append(f"- 描述: {kdj.description}")
        
        if 'patterns' in context and context['patterns']:
            prompt_parts.append(f"\n形态识别:")
            for pattern in context['patterns'][:5]:
                prompt_parts.append(f"- {pattern.pattern_name}: {pattern.description}")
                prompt_parts.append(f"  置信度: {pattern.confidence:.2f}")
                prompt_parts.append(f"  目标价: {pattern.target_price}")
                prompt_parts.append(f"  止损价: {pattern.stop_loss}")
        
        if 'volume_price' in context:
            vp = context['volume_price']
            if 'volume_trend' in vp:
                prompt_parts.append(f"\n成交量趋势:")
                prompt_parts.append(f"- 趋势: {vp['volume_trend'].get('volume_trend', '未知')}")
                prompt_parts.append(f"- 描述: {vp['volume_trend'].get('volume_description', '')}")
            
            if 'correlation' in vp:
                prompt_parts.append(f"\n量价相关性:")
                prompt_parts.append(f"- 类型: {vp['correlation'].get('correlation_type', '未知')}")
                prompt_parts.append(f"- 相关系数: {vp['correlation'].get('correlation_coefficient', 0)}")
                prompt_parts.append(f"- 描述: {vp['correlation'].get('correlation_description', '')}")
            
            if 'accumulation' in vp:
                prompt_parts.append(f"\n资金累积:")
                prompt_parts.append(f"- 状态: {vp['accumulation'].get('accumulation_status', '未知')}")
                prompt_parts.append(f"- 描述: {vp['accumulation'].get('accumulation_description', '')}")
        
        prompt_parts.append("\n\n请基于以上数据进行分析，并给出明确的建议。")
        
        return "\n".join(prompt_parts)
    
    def analyze(self, context: Dict[str, Any]) -> Tuple[bool, str, Optional[AgentAnalysis]]:
        try:
            if not self.config.enable_llm_analysis:
                return False, "LLM分析未启用", None
            
            self.logger.info(f"{self.agent_name} 开始分析...")
            
            system_prompt = self._build_system_prompt(context)
            user_prompt = self._build_user_prompt(context)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.provider.chat(messages)
            
            analysis_result = self._parse_response(response, context)
            
            self.logger.info(f"{self.agent_name} 分析完成")
            
            return True, "分析成功", analysis_result
            
        except Exception as e:
            self.logger.error(f"{self.agent_name} 分析失败: {str(e)}")
            return False, str(e), None
    
    def _parse_response(self, response: str, context: Dict[str, Any]) -> AgentAnalysis:
        import re
        
        recommendation = "持有"
        confidence = 0.5
        risk_level = "中"
        reasoning = response
        
        rec_match = re.search(r'建议[：:]\s*(买入|卖出|持有)', response)
        if rec_match:
            recommendation = rec_match.group(1)
        
        conf_match = re.search(r'置信度[：:]\s*([0-9.]+)', response)
        if conf_match:
            try:
                confidence = float(conf_match.group(1))
                confidence = max(0, min(1, confidence))
            except ValueError:
                pass
        
        risk_match = re.search(r'风险等级[：:]\s*(低|中|高)', response)
        if risk_match:
            risk_level = risk_match.group(1)
        
        reasoning_match = re.search(r'推理过程[：:]\s*(.+?)(?=建议|置信度|风险等级|$)', response, re.DOTALL)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
        
        return AgentAnalysis(
            agent_name=self.agent_name,
            agent_type=self.agent_type,
            analysis_result={'raw_response': response},
            confidence=confidence,
            recommendation=recommendation,
            risk_level=risk_level,
            reasoning=reasoning
        )
