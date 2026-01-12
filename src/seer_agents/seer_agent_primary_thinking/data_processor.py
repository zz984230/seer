import os
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import hashlib
from .models import ExpertQuote, KnowledgeEntry, AnalysisDimension, AnalysisFramework, MainForceBehavior, TradingStrategy
from seer.logger import logger


class DataProcessor:
    def __init__(self, src_data_dir: str):
        self.src_data_dir = src_data_dir
        self.logger = logger
        self.processed_quotes: List[ExpertQuote] = []
        self.knowledge_base: List[KnowledgeEntry] = []
    
    def _read_markdown_file(self, file_path: str) -> Optional[str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"读取文件失败: {file_path}, 错误: {str(e)}")
            return None
    
    def _extract_video_info(self, content: str) -> Dict[str, Any]:
        info = {
            'expert_name': '领居大爷',
            'video_title': '',
            'video_date': ''
        }
        
        title_match = re.search(r'《([^》]+)》', content)
        if title_match:
            info['video_title'] = title_match.group(1)
        
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', content)
        if date_match:
            info['video_date'] = date_match.group(1)
        
        return info
    
    def _extract_summary(self, content: str) -> str:
        summary_match = re.search(r'###?\s*\d+\.\s*视频的主要内容摘要\s*\n+(.*?)(?=###?\s*\d+\.|$)', content, re.DOTALL)
        if summary_match:
            summary = summary_match.group(1).strip()
            return re.sub(r'\n+', '\n', summary)
        
        summary_match = re.search(r'\*\*\d+\.\s*视频的主要内容摘要\s*\*\*\s*\n+(.*?)(?=\*\*\d+\.|$)', content, re.DOTALL)
        if summary_match:
            summary = summary_match.group(1).strip()
            return re.sub(r'\n+', '\n', summary)
        
        return ""
    
    def _extract_key_points(self, content: str) -> List[str]:
        key_points = []
        
        patterns = [
            r'###?\s*\d+\.\s*关键信息和要点\s*\n+(.*?)(?=###?\s*\d+\.|$)',
            r'\*\*\d+\.\s*关键信息和要点\s*\*\*\s*\n+(.*?)(?=\*\*\d+\.|$)',
            r'###?\s*\d+\.\s*关键信息和要点\s*\n+(.*?)(?=###?\s*\d+\.|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                points_text = match.group(1)
                points = re.findall(r'[✓✅●-]\s*(.+?)(?=\n|$)', points_text)
                key_points.extend([p.strip() for p in points if p.strip()])
                break
        
        return list(set(key_points))
    
    def _extract_core_concepts(self, content: str, key_points: List[str]) -> List[str]:
        concepts = []
        
        concept_keywords = [
            '主力', '洗盘', '拉升', '出货', '建仓', '吸筹', 
            '拖拉机单', '主升浪', '颈线', '箱体', '诱多',
            '假象', '对敲', '日内洗盘', '试盘', '蓄势',
            '金叉', '死叉', '超买', '超卖', '背离', '背离'
        ]
        
        for keyword in concept_keywords:
            if keyword in content:
                concepts.append(keyword)
        
        return list(set(concepts))
    
    def _extract_technical_patterns(self, content: str) -> List[str]:
        patterns = []
        
        pattern_keywords = [
            '颈线突破结构', '大长腿买入法', 'N型结构', 
            '上影线+实体阳线结构', '低位阳包阴', '箱体结构突破',
            '头肩顶', '头肩底', '双顶', '双底', '三角形整理',
            '上升楔形', '下降楔形', '收敛三角形', '下降三角形',
            '缩量加速', '放量大阳线', '高位分歧K线', '流星线',
            '吊颈线', '连续高位横盘', '大阴线', '小阴线'
        ]
        
        for keyword in pattern_keywords:
            if keyword in content:
                patterns.append(keyword)
        
        return list(set(patterns))
    
    def _extract_trading_strategies(self, content: str) -> List[str]:
        strategies = []
        
        strategy_patterns = [
            r'低位拖拉机单\s*→\s*([^。\n]+)',
            r'高位拖拉机单\s*→\s*([^。\n]+)',
            r'坚定持股\s*→\s*([^。\n]+)',
            r'顺势而为\s*→\s*([^。\n]+)',
            r'分批建仓\s*→\s*([^。\n]+)',
            r'倒推法\s*→\s*([^。\n]+)',
            r'线下离场\s*→\s*([^。\n]+)',
            r'线上进场\s*→\s*([^。\n]+)'
        ]
        
        for pattern in strategy_patterns:
            matches = re.findall(pattern, content)
            strategies.extend([m.strip() for m in matches if m.strip()])
        
        return list(set(strategies))
    
    def _extract_risk_warnings(self, content: str) -> List[str]:
        warnings = []
        
        warning_patterns = [
            r'风险提示\s*[:：]\s*([^。\n]+)',
            r'风险警示\s*[:：]\s*([^。\n]+)',
            r'警告\s*[:：]\s*([^。\n]+)',
            r'切勿([^。\n]+)',
            r'避免([^。\n]+)',
            r'不要([^。\n]+)',
            r'风险极高',
            r'易被套',
            r'容易被套'
        ]
        
        for pattern in warning_patterns:
            matches = re.findall(pattern, content)
            warnings.extend([m.strip() for m in matches if m.strip()])
        
        return list(set(warnings))
    
    def _extract_main_force_behavior(self, content: str) -> List[str]:
        behaviors = []
        
        behavior_keywords = [
            '拖拉机单', '告知手法', '点火', '诱多',
            '主动补货区', '拦截吃货', '打压吃货', '拆单出货',
            '引导性拉升', '假突破', '假回撤', '对敲',
            '日内洗盘', '技术结构洗盘', '休克式交易',
            '试盘', '蓄势', '调仓', '自救'
        ]
        
        for keyword in behavior_keywords:
            if keyword in content:
                behaviors.append(keyword)
        
        return list(set(behaviors))
    
    def _extract_market_logic(self, content: str) -> List[str]:
        logic_points = []
        
        logic_patterns = [
            r'([^。\n]+)\s*=\s*([^。\n]+)',
            r'([^。\n]+)\s*代表\s*([^。\n]+)',
            r'([^。\n]+)\s*意味着\s*([^。\n]+)',
            r'([^。\n]+)\s*说明\s*([^。\n]+)'
        ]
        
        for pattern in logic_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match) == 2:
                    logic_point = f"{match[0].strip()} = {match[1].strip()}"
                    logic_points.append(logic_point)
        
        return list(set(logic_points))
    
    def _generate_entry_id(self, content: str) -> str:
        hash_obj = hashlib.md5(content.encode('utf-8'))
        return hash_obj.hexdigest()[:16]
    
    def _deduplicate_quotes(self, quotes: List[ExpertQuote]) -> List[ExpertQuote]:
        seen = set()
        unique_quotes = []
        
        for quote in quotes:
            key = f"{quote.expert_name}_{quote.video_title}_{quote.video_date}"
            if key not in seen:
                seen.add(key)
                unique_quotes.append(quote)
        
        return unique_quotes
    
    def _standardize_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        text = text.strip()
        return text
    
    def process_single_file(self, file_path: str) -> Optional[ExpertQuote]:
        try:
            content = self._read_markdown_file(file_path)
            if not content:
                return None
            
            video_info = self._extract_video_info(content)
            summary = self._extract_summary(content)
            key_points = self._extract_key_points(content)
            core_concepts = self._extract_core_concepts(content, key_points)
            technical_patterns = self._extract_technical_patterns(content)
            trading_strategies = self._extract_trading_strategies(content)
            risk_warnings = self._extract_risk_warnings(content)
            main_force_behavior = self._extract_main_force_behavior(content)
            market_logic = self._extract_market_logic(content)
            
            quote = ExpertQuote(
                expert_name=video_info['expert_name'],
                video_title=video_info['video_title'],
                video_date=video_info['video_date'],
                summary=self._standardize_text(summary),
                key_points=[self._standardize_text(kp) for kp in key_points],
                core_concepts=core_concepts,
                technical_patterns=technical_patterns,
                trading_strategies=[self._standardize_text(ts) for ts in trading_strategies],
                risk_warnings=[self._standardize_text(rw) for rw in risk_warnings],
                main_force_behavior=main_force_behavior,
                market_logic=[self._standardize_text(ml) for ml in market_logic]
            )
            
            return quote
            
        except Exception as e:
            self.logger.error(f"处理文件失败: {file_path}, 错误: {str(e)}")
            return None
    
    def process_all_files(self) -> Tuple[bool, str, List[ExpertQuote]]:
        try:
            self.logger.info(f"开始处理目录: {self.src_data_dir}")
            
            if not os.path.exists(self.src_data_dir):
                return False, f"目录不存在: {self.src_data_dir}", []
            
            md_files = list(Path(self.src_data_dir).glob("*.md"))
            
            if not md_files:
                return False, f"未找到Markdown文件: {self.src_data_dir}", []
            
            self.logger.info(f"找到 {len(md_files)} 个Markdown文件")
            
            processed_quotes = []
            
            for md_file in md_files:
                self.logger.info(f"处理文件: {md_file.name}")
                quote = self.process_single_file(str(md_file))
                if quote:
                    processed_quotes.append(quote)
            
            deduplicated_quotes = self._deduplicate_quotes(processed_quotes)
            
            self.processed_quotes = deduplicated_quotes
            self.logger.info(f"处理完成，共 {len(deduplicated_quotes)} 条专家语录（去重后）")
            
            return True, f"成功处理 {len(deduplicated_quotes)} 条语录", deduplicated_quotes
            
        except Exception as e:
            self.logger.error(f"处理所有文件失败: {str(e)}")
            return False, str(e), []
    
    def save_processed_data(self, output_path: str) -> Tuple[bool, str]:
        try:
            data_dicts = [quote.model_dump() for quote in self.processed_quotes]
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_dicts, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"数据已保存: {output_path}")
            return True, "保存成功"
            
        except Exception as e:
            self.logger.error(f"保存数据失败: {str(e)}")
            return False, str(e)
    
    def get_statistics(self) -> Dict[str, Any]:
        if not self.processed_quotes:
            return {}
        
        stats = {
            'total_quotes': len(self.processed_quotes),
            'expert_names': list(set([q.expert_name for q in self.processed_quotes])),
            'date_range': {
                'earliest': min([q.video_date for q in self.processed_quotes if q.video_date]),
                'latest': max([q.video_date for q in self.processed_quotes if q.video_date])
            },
            'total_key_points': sum([len(q.key_points) for q in self.processed_quotes]),
            'total_technical_patterns': sum([len(q.technical_patterns) for q in self.processed_quotes]),
            'total_trading_strategies': sum([len(q.trading_strategies) for q in self.processed_quotes]),
            'total_risk_warnings': sum([len(q.risk_warnings) for q in self.processed_quotes]),
            'unique_concepts': list(set([c for q in self.processed_quotes for c in q.core_concepts])),
            'unique_patterns': list(set([p for q in self.processed_quotes for p in q.technical_patterns])),
            'unique_strategies': list(set([s for q in self.processed_quotes for s in q.trading_strategies]))
        }
        
        return stats
