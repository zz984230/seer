import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from seer_agents.seer_agent_primary_thinking.data_processor import DataProcessor
from seer_agents.seer_agent_primary_thinking.knowledge_base import KnowledgeBase
from seer.logger import logger


def main():
    src_data_dir = project_root / "src" / "seer_agents" / "seer_agent_primary_thinking" / "src_data"
    output_dir = project_root / "data" / "primary_thinking"
    
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("开始构建B站投资专家思维知识库")
    logger.info("=" * 60)
    
    processor = DataProcessor(str(src_data_dir))
    
    logger.info("步骤1: 处理专家语录文件...")
    success, msg, quotes = processor.process_all_files()
    
    if not success:
        logger.error(f"处理语录文件失败: {msg}")
        return
    
    logger.info(f"成功处理 {len(quotes)} 条专家语录")
    
    stats = processor.get_statistics()
    logger.info("语录统计信息:")
    logger.info(f"  - 总语录数: {stats['total_quotes']}")
    logger.info(f"  - 专家名称: {', '.join(stats['expert_names'])}")
    logger.info(f"  - 日期范围: {stats['date_range']['earliest']} ~ {stats['date_range']['latest']}")
    logger.info(f"  - 总关键点数: {stats['total_key_points']}")
    logger.info(f"  - 总技术形态数: {stats['total_technical_patterns']}")
    logger.info(f"  - 总交易策略数: {stats['total_trading_strategies']}")
    logger.info(f"  - 总风险提示数: {stats['total_risk_warnings']}")
    logger.info(f"  - 唯一概念数: {len(stats['unique_concepts'])}")
    logger.info(f"  - 唯一形态数: {len(stats['unique_patterns'])}")
    logger.info(f"  - 唯一策略数: {len(stats['unique_strategies'])}")
    
    logger.info("")
    logger.info("步骤2: 保存处理后的语录数据...")
    quotes_output_path = str(output_dir / "processed_quotes.json")
    success, msg = processor.save_processed_data(quotes_output_path)
    
    if not success:
        logger.error(f"保存语录数据失败: {msg}")
        return
    
    logger.info(f"语录数据已保存: {quotes_output_path}")
    
    logger.info("")
    logger.info("步骤3: 构建知识库...")
    knowledge_base = KnowledgeBase()
    
    success, msg = knowledge_base.add_knowledge_from_quotes(quotes)
    
    if not success:
        logger.error(f"添加知识到知识库失败: {msg}")
        return
    
    logger.info(f"成功添加知识到知识库")
    
    kb_stats = knowledge_base.get_statistics()
    logger.info("知识库统计信息:")
    logger.info(f"  - 知识条目数: {kb_stats['knowledge_entries']}")
    logger.info(f"  - 分析维度数: {kb_stats['analysis_dimensions']}")
    logger.info(f"  - 分析框架数: {kb_stats['analysis_frameworks']}")
    logger.info(f"  - 主力行为数: {kb_stats['main_force_behaviors']}")
    logger.info(f"  - 交易策略数: {kb_stats['trading_strategies']}")
    logger.info(f"  - 知识分类: {', '.join(kb_stats['categories'])}")
    logger.info(f"  - 总标签数: {kb_stats['total_tags']}")
    
    logger.info("")
    logger.info("步骤4: 保存知识库...")
    kb_output_path = str(output_dir / "knowledge_base.json")
    success, msg = knowledge_base.save_knowledge_base(kb_output_path)
    
    if not success:
        logger.error(f"保存知识库失败: {msg}")
        return
    
    logger.info(f"知识库已保存: {kb_output_path}")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("知识库构建完成！")
    logger.info("=" * 60)
    logger.info("")
    logger.info("生成文件:")
    logger.info(f"  1. 处理后的语录: {quotes_output_path}")
    logger.info(f"  2. 知识库文件: {kb_output_path}")
    logger.info("")
    logger.info("知识库包含以下内容:")
    logger.info("  - 6个分析维度（主力行为、技术形态、量价关系等）")
    logger.info("  - 4个分析框架（主力行为、技术形态、主升浪、时间周期）")
    logger.info("  - 4个主力行为（建仓、洗盘、拉升、出货）")
    logger.info("  - 4个交易策略（起涨结构、主力行为、时间节点、风险控制）")
    logger.info("")
    logger.info("下一步:")
    logger.info("  1. 使用PrimaryThinkingAgent进行个股分析")
    logger.info("  2. 通过知识库检索相关专家思维")
    logger.info("  3. 结合多Agent分析结果生成综合报告")


if __name__ == "__main__":
    main()
