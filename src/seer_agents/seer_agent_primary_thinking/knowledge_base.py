from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import json
import os
from datetime import datetime
from .models import (
    ExpertQuote, KnowledgeEntry, AnalysisDimension, 
    AnalysisFramework, MainForceBehavior, TradingStrategy
)
from seer.logger import logger


class KnowledgeBase:
    def __init__(self):
        self.logger = logger
        self.knowledge_entries: List[KnowledgeEntry] = []
        self.analysis_dimensions: List[AnalysisDimension] = []
        self.analysis_frameworks: List[AnalysisFramework] = []
        self.main_force_behaviors: List[MainForceBehavior] = []
        self.trading_strategies: List[TradingStrategy] = []
        
        self._initialize_base_knowledge()
    
    def _initialize_base_knowledge(self):
        self._build_analysis_dimensions()
        self._build_analysis_frameworks()
        self._build_main_force_behaviors()
        self._build_trading_strategies()
    
    def _build_analysis_dimensions(self):
        dimensions = [
            AnalysisDimension(
                dimension_name="主力行为分析",
                indicators=["拖拉机单", "主动补货区", "拦截吃货", "打压吃货", 
                          "拆单出货", "引导性拉升", "日内洗盘", "技术结构洗盘"],
                importance=0.95,
                description="分析主力资金在不同阶段的操作手法和意图"
            ),
            AnalysisDimension(
                dimension_name="技术形态识别",
                indicators=["颈线突破", "大长腿", "N型结构", "阳包阴", 
                          "头肩顶/底", "双顶/双底", "三角形整理", "楔形"],
                importance=0.90,
                description="识别股价走势中的关键技术形态，判断买卖时机"
            ),
            AnalysisDimension(
                dimension_name="量价关系分析",
                indicators=["成交量", "换手率", "量增价涨", "量增价跌", 
                          "量减价涨", "量减价跌", "缩量横盘"],
                importance=0.88,
                description="分析成交量与价格的关系，判断资金流向和趋势强度"
            ),
            AnalysisDimension(
                dimension_name="技术指标分析",
                indicators=["MACD", "RSI", "KDJ", "均线系统", "趋势线"],
                importance=0.85,
                description="通过技术指标判断超买超卖、趋势方向和买卖信号"
            ),
            AnalysisDimension(
                dimension_name="市场环境分析",
                indicators=["大盘走势", "板块轮动", "政策导向", "市场情绪"],
                importance=0.80,
                description="分析整体市场环境和板块轮动，把握投资节奏"
            ),
            AnalysisDimension(
                dimension_name="风险控制评估",
                indicators=["止损位", "仓位管理", "风险等级", "最大回撤"],
                importance=0.92,
                description="评估投资风险，制定合理的风险控制策略"
            )
        ]
        
        self.analysis_dimensions = dimensions
        self.logger.info(f"初始化分析维度: {len(dimensions)} 个")
    
    def _build_analysis_frameworks(self):
        frameworks = [
            AnalysisFramework(
                framework_name="主力行为分析框架",
                phases=["建仓阶段", "洗盘阶段", "拉升阶段", "出货阶段"],
                decision_logic="根据主力资金在不同阶段的特征，判断当前股价所处的阶段和后续走势",
                key_factors=[
                    "拖拉机单位置（低位=机会，高位=陷阱）",
                    "主动补货区识别（压力位附近、连续放量、不突破）",
                    "吃货时间长短（时间短=仓位轻，时间长=仓位重）",
                    "洗盘特征（多日震荡、阴线多于阳线、结构完好）",
                    "出货信号（大阳线出货、连续放量后滞涨、高位分歧）"
                ]
            ),
            AnalysisFramework(
                framework_name="技术形态分析框架",
                phases=["形态识别", "信号确认", "目标测算", "风险控制"],
                decision_logic="通过识别关键技术形态，结合成交量确认，测算目标价格并设置止损",
                key_factors=[
                    "起涨结构（颈线突破、大长腿、N型、阳包阴）",
                    "逃顶结构（缩量加速、放量大阳线、高位分歧、吊颈线）",
                    "形态位置（底部起涨 vs 上涨途中）",
                    "成交量配合（放量突破 vs 缩量突破）",
                    "置信度评估（形态完整性和对称性）"
                ]
            ),
            AnalysisFramework(
                framework_name="主升浪分析框架",
                phases=["突破后调整期", "洗盘后拉升期", "加速出货期"],
                decision_logic="识别主升浪的三个区间，根据不同区间采取不同的持股策略",
                key_factors=[
                    "第一区间：突破后调整（30%-50%调整，恶性洗盘）",
                    "第二区间：洗盘后拉升（斜率>45°用5日线，<45°用10日线）",
                    "第三区间：加速出货（宽幅震荡、鱼尾行情、主力出货）",
                    "均线风控（线下离场，线上进场）",
                    "主力是否出货（核心判断标准）"
                ]
            ),
            AnalysisFramework(
                framework_name="时间周期分析框架",
                phases=["早盘观察", "尾盘决策", "次日执行"],
                decision_logic="利用关键时间节点进行决策，提高资金效率",
                key_factors=[
                    "上午10点前：观察市场风险，判断板块启动",
                    "下午2点半后：判断主力资金动向，决定次日操作",
                    "次日早盘：确认趋势延续性，决定加仓或减仓",
                    "避免上午10点后进场（被动接盘）",
                    "下午2点半后进场（主动出击）"
                ]
            )
        ]
        
        self.analysis_frameworks = frameworks
        self.logger.info(f"初始化分析框架: {len(frameworks)} 个")
    
    def _build_main_force_behaviors(self):
        behaviors = [
            MainForceBehavior(
                behavior_type="建仓",
                characteristics=[
                    "选择深跌股（跌幅50%-70%）",
                    "拉涨停激活沉睡筹码",
                    "制造恐慌盘吓退散户",
                    "拦截吃货（买5买4大单托底）",
                    "打压吃货（单根量放大）"
                ],
                identification_methods=[
                    "低位箱体震荡形态",
                    "主动补货区（压力位附近、连续放量、红肥绿瘦）",
                    "吃货时间长短判断仓位轻重",
                    "分批吸筹而非满仓建仓"
                ],
                countermeasures=[
                    "不要盲目跟随主力建仓",
                    "关注市场主线板块而非个股",
                    "等待底部箱体突破+大阳线信号",
                    "使用倒推法验证主力吸筹完成"
                ]
            ),
            MainForceBehavior(
                behavior_type="洗盘",
                characteristics=[
                    "启动前洗盘：剧烈震荡、清洗不坚定散户",
                    "拉升后洗盘：横盘或缩量调整、消化获利盘",
                    "多日震荡而非单日波动",
                    "阴线多于阳线、成交量萎缩",
                    "不破坏原有上升结构"
                ],
                identification_methods=[
                    "收敛三角形或下降三角形整理",
                    "震荡+缩量+结构完整",
                    "大阴线破坏结构=出货而非洗盘",
                    "洗盘阶段是最佳进场点"
                ],
                countermeasures=[
                    "不追高、不恐慌",
                    "在洗盘末期（缩量+阳线突破）介入",
                    "学会看结构而非看K线",
                    "观察是否被洗出散户"
                ]
            ),
            MainForceBehavior(
                behavior_type="拉升",
                characteristics=[
                    "卖四买六或卖二买四大单对倒",
                    "快速突破阻力位",
                    "涨停板或大阳线出现",
                    "频繁做上影线（日内洗盘）",
                    "抬高市场综合成本"
                ],
                identification_methods=[
                    "涨停板或大阳线",
                    "放量突破关键阻力位",
                    "上影线频繁但未破前高",
                    "阳线实体小+上影线长=试盘",
                    "斜率>45°强势拉升"
                ],
                countermeasures=[
                    "识别拉升阶段，顺势而为",
                    "关注斜率选择风控均线",
                    "警惕连续上影线未破前高=顶部信号",
                    "主力未出货按技术结构持股"
                ]
            ),
            MainForceBehavior(
                behavior_type="出货",
                characteristics=[
                    "在大阳线内部出货（而非阴线）",
                    "拆单出货（大单拆成小单）",
                    "诱多拉升（快速拉高6个点以上）",
                    "高位震荡横盘",
                    "制造假突破或假回撤"
                ],
                identification_methods=[
                    "连续放量大阳线后滞涨",
                    "高位分歧K线（流星线）",
                    "吊颈线（尤其尾盘出现）",
                    "连续高位横盘小K线后转阴",
                    "缩量加速上涨（鱼尾行情）"
                ],
                countermeasures=[
                    "见放量大阳线立即离场",
                    "警惕高位拖拉机单=诱多陷阱",
                    "不要在连续上涨途中追高",
                    "识别主力出货后及时止损"
                ]
            )
        ]
        
        self.main_force_behaviors = behaviors
        self.logger.info(f"初始化主力行为: {len(behaviors)} 个")
    
    def _build_trading_strategies(self):
        strategies = [
            TradingStrategy(
                strategy_name="起涨结构买入法",
                entry_conditions=[
                    "股价处于底部区域",
                    "出现颈线突破+放量阳线",
                    "大长腿买入法（实体长、下影线长）",
                    "N型结构（突破-回踩-再拉起）",
                    "上影线+实体阳线（试盘+吸筹）",
                    "低位阳包阴（假阴后转阳）"
                ],
                exit_conditions=[
                    "主力出货信号出现",
                    "破位关键支撑位",
                    "达到目标价格",
                    "出现逃顶结构"
                ],
                risk_control=[
                    "设置止损位",
                    "控制仓位（初期小仓位试错）",
                    "避免连续上涨途中追高",
                    "结合市场环境和热点板块"
                ],
                success_rate=0.75
            ),
            TradingStrategy(
                strategy_name="主力行为跟随法",
                entry_conditions=[
                    "识别主力建仓完成信号",
                    "等待洗盘末期介入",
                    "确认主力未出货",
                    "观察拖拉机单位置（低位=机会）"
                ],
                exit_conditions=[
                    "主力开始出货",
                    "回调时间过长（恶性调整）",
                    "调整波段远大于拉升波段",
                    "结构被破坏"
                ],
                risk_control=[
                    "不要盲目跟随主力建仓",
                    "关注吃货时间判断空间",
                    "区分良性调整与恶性调整",
                    "主力离场后立即止损"
                ],
                success_rate=0.80
            ),
            TradingStrategy(
                strategy_name="时间节点决策法",
                entry_conditions=[
                    "上午10点前观察市场风险",
                    "下午2点半后判断主力动向",
                    "确认趋势延续性后次日早盘加仓"
                ],
                exit_conditions=[
                    "尾盘出现弱势信号",
                    "次日早盘趋势未延续",
                    "大盘企稳条件不满足"
                ],
                risk_control=[
                    "避免上午10点后被动接盘",
                    "下午2点半后主动出击",
                    "等待大盘企稳再出手",
                    "加入自选池等待信号"
                ],
                success_rate=0.70
            ),
            TradingStrategy(
                strategy_name="风险控制优先法",
                entry_conditions=[
                    "确认盘整充分（至少5天）",
                    "出现安全垫突破（密集成交区）",
                    "风险等级评估为低或中"
                ],
                exit_conditions=[
                    "破位止损",
                    "主力出货信号",
                    "风险等级上升至高"
                ],
                risk_control=[
                    "严格设置止损位",
                    "分批建仓控制风险",
                    "不盲目抄底",
                    "优先保住本金"
                ],
                success_rate=0.85
            )
        ]
        
        self.trading_strategies = strategies
        self.logger.info(f"初始化交易策略: {len(strategies)} 个")
    
    def add_knowledge_from_quotes(self, quotes: List[ExpertQuote]) -> Tuple[bool, str]:
        try:
            entry_count = 0
            
            for quote in quotes:
                for key_point in quote.key_points:
                    entry = KnowledgeEntry(
                        entry_id=self._generate_entry_id(quote.video_title, key_point),
                        category="技术分析",
                        title=f"{quote.video_title} - {key_point[:30]}",
                        content=key_point,
                        tags=quote.core_concepts + quote.technical_patterns,
                        source=f"{quote.expert_name} - {quote.video_date}",
                        confidence=0.85
                    )
                    self.knowledge_entries.append(entry)
                    entry_count += 1
                
                for strategy in quote.trading_strategies:
                    entry = KnowledgeEntry(
                        entry_id=self._generate_entry_id(quote.video_title, strategy),
                        category="交易策略",
                        title=f"{quote.video_title} - {strategy[:30]}",
                        content=strategy,
                        tags=quote.core_concepts,
                        source=f"{quote.expert_name} - {quote.video_date}",
                        confidence=0.90
                    )
                    self.knowledge_entries.append(entry)
                    entry_count += 1
                
                for warning in quote.risk_warnings:
                    entry = KnowledgeEntry(
                        entry_id=self._generate_entry_id(quote.video_title, warning),
                        category="风险控制",
                        title=f"{quote.video_title} - {warning[:30]}",
                        content=warning,
                        tags=["风险提示"],
                        source=f"{quote.expert_name} - {quote.video_date}",
                        confidence=0.95
                    )
                    self.knowledge_entries.append(entry)
                    entry_count += 1
            
            self.logger.info(f"从专家语录添加 {entry_count} 条知识")
            return True, f"成功添加 {entry_count} 条知识"
            
        except Exception as e:
            self.logger.error(f"添加知识失败: {str(e)}")
            return False, str(e)
    
    def _generate_entry_id(self, title: str, content: str) -> str:
        import hashlib
        combined = f"{title}_{content[:50]}"
        hash_obj = hashlib.md5(combined.encode('utf-8'))
        return hash_obj.hexdigest()[:16]
    
    def search_knowledge(self, query: str, category: Optional[str] = None, 
                      limit: int = 10) -> List[KnowledgeEntry]:
        query_lower = query.lower()
        
        results = []
        for entry in self.knowledge_entries:
            if category and entry.category != category:
                continue
            
            score = 0
            if query_lower in entry.title.lower():
                score += 3
            if query_lower in entry.content.lower():
                score += 5
            for tag in entry.tags:
                if query_lower in tag.lower():
                    score += 2
            
            if score > 0:
                results.append((entry, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, score in results[:limit]]
    
    def get_analysis_dimensions(self) -> List[AnalysisDimension]:
        return self.analysis_dimensions
    
    def get_analysis_frameworks(self) -> List[AnalysisFramework]:
        return self.analysis_frameworks
    
    def get_main_force_behaviors(self) -> List[MainForceBehavior]:
        return self.main_force_behaviors
    
    def get_trading_strategies(self) -> List[TradingStrategy]:
        return self.trading_strategies
    
    def get_knowledge_by_category(self, category: str) -> List[KnowledgeEntry]:
        return [entry for entry in self.knowledge_entries if entry.category == category]
    
    def save_knowledge_base(self, output_path: str) -> Tuple[bool, str]:
        try:
            data = {
                'knowledge_entries': [entry.model_dump() for entry in self.knowledge_entries],
                'analysis_dimensions': [dim.model_dump() for dim in self.analysis_dimensions],
                'analysis_frameworks': [fw.model_dump() for fw in self.analysis_frameworks],
                'main_force_behaviors': [behavior.model_dump() for behavior in self.main_force_behaviors],
                'trading_strategies': [strategy.model_dump() for strategy in self.trading_strategies],
                'metadata': {
                    'total_entries': len(self.knowledge_entries),
                    'total_dimensions': len(self.analysis_dimensions),
                    'total_frameworks': len(self.analysis_frameworks),
                    'total_behaviors': len(self.main_force_behaviors),
                    'total_strategies': len(self.trading_strategies),
                    'created_at': datetime.now().isoformat()
                }
            }
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"知识库已保存: {output_path}")
            return True, "保存成功"
            
        except Exception as e:
            self.logger.error(f"保存知识库失败: {str(e)}")
            return False, str(e)
    
    def load_knowledge_base(self, input_path: str) -> Tuple[bool, str]:
        try:
            if not os.path.exists(input_path):
                self.logger.warning(f"知识库文件不存在: {input_path}")
                return False, "文件不存在"
            
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.knowledge_entries = [
                KnowledgeEntry(**entry) 
                for entry in data.get('knowledge_entries', [])
            ]
            self.analysis_dimensions = [
                AnalysisDimension(**dim) 
                for dim in data.get('analysis_dimensions', [])
            ]
            self.analysis_frameworks = [
                AnalysisFramework(**fw) 
                for fw in data.get('analysis_frameworks', [])
            ]
            self.main_force_behaviors = [
                MainForceBehavior(**behavior) 
                for behavior in data.get('main_force_behaviors', [])
            ]
            self.trading_strategies = [
                TradingStrategy(**strategy) 
                for strategy in data.get('trading_strategies', [])
            ]
            
            self.logger.info(f"知识库已加载: {input_path}")
            return True, "加载成功"
            
        except Exception as e:
            self.logger.error(f"加载知识库失败: {str(e)}")
            return False, str(e)
    
    def get_statistics(self) -> Dict[str, Any]:
        return {
            'knowledge_entries': len(self.knowledge_entries),
            'analysis_dimensions': len(self.analysis_dimensions),
            'analysis_frameworks': len(self.analysis_frameworks),
            'main_force_behaviors': len(self.main_force_behaviors),
            'trading_strategies': len(self.trading_strategies),
            'categories': list(set([entry.category for entry in self.knowledge_entries])),
            'total_tags': len(set([tag for entry in self.knowledge_entries for tag in entry.tags]))
        }
