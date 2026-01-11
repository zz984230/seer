import os
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
import seaborn as sns
from .models import ComprehensiveAnalysis, AnalysisReport
from .config import settings
from seer.logger import logger

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class TechAnalysisReporter:
    def __init__(self):
        self.logger = logger
        self.config = settings.report
        self.report_dir = self.config.report_dir
        os.makedirs(self.report_dir, exist_ok=True)
    
    def _generate_chart_paths(self, analysis: ComprehensiveAnalysis) -> List[str]:
        chart_paths = []
        
        if not self.config.enable_charts:
            return chart_paths
        
        try:
            stock_data = analysis.stock_data
            if not stock_data:
                return chart_paths
            
            dates = [datetime.strptime(item.date, "%Y-%m-%d") for item in stock_data]
            close_prices = [item.close_price for item in stock_data]
            volumes = [item.volume for item in stock_data]
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(self.config.chart_width / 100, self.config.chart_height / 100), dpi=self.config.chart_dpi)
            
            ax1.plot(dates, close_prices, label='收盘价', linewidth=1.5)
            ax1.set_title(f"{analysis.stock_name}({analysis.stock_code}) 价格走势")
            ax1.set_ylabel('价格')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            if analysis.macd:
                ax1_twin = ax1.twinx()
                ax1_twin.plot(dates, analysis.macd.dif, label='DIF', color='orange', alpha=0.7)
                ax1_twin.plot(dates, analysis.macd.dea, label='DEA', color='purple', alpha=0.7)
                ax1_twin.set_ylabel('MACD')
                ax1_twin.legend(loc='upper left')
            
            colors = ['red' if i > 0 and volumes[i] > volumes[i-1] else 'green' for i in range(len(volumes))]
            ax2.bar(dates, volumes, color=colors, alpha=0.6)
            ax2.set_title('成交量')
            ax2.set_ylabel('成交量')
            ax2.grid(True, alpha=0.3)
            
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            
            price_chart_path = os.path.join(self.report_dir, f"{analysis.stock_code}_price_chart.png")
            plt.savefig(price_chart_path, dpi=self.config.chart_dpi, bbox_inches='tight')
            plt.close()
            
            chart_paths.append({
                'type': 'price_volume',
                'path': price_chart_path,
                'title': '价格与成交量走势图'
            })
            
            if analysis.rsi:
                fig, ax = plt.subplots(figsize=(self.config.chart_width / 100, self.config.chart_height / 100 / 2), dpi=self.config.chart_dpi)
                
                ax.plot(dates, analysis.rsi.rsi6, label='RSI6', alpha=0.8)
                ax.plot(dates, analysis.rsi.rsi12, label='RSI12', alpha=0.8)
                ax.plot(dates, analysis.rsi.rsi24, label='RSI24', alpha=0.8)
                
                ax.axhline(y=70, color='r', linestyle='--', alpha=0.5, label='超买线(70)')
                ax.axhline(y=30, color='g', linestyle='--', alpha=0.5, label='超卖线(30)')
                
                ax.set_title(f"{analysis.stock_name}({analysis.stock_code}) RSI指标")
                ax.set_ylabel('RSI')
                ax.set_ylim(0, 100)
                ax.grid(True, alpha=0.3)
                ax.legend()
                
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
                
                plt.tight_layout()
                
                rsi_chart_path = os.path.join(self.report_dir, f"{analysis.stock_code}_rsi_chart.png")
                plt.savefig(rsi_chart_path, dpi=self.config.chart_dpi, bbox_inches='tight')
                plt.close()
                
                chart_paths.append({
                    'type': 'rsi',
                    'path': rsi_chart_path,
                    'title': 'RSI指标图'
                })
            
            if analysis.kdj:
                fig, ax = plt.subplots(figsize=(self.config.chart_width / 100, self.config.chart_height / 100 / 2), dpi=self.config.chart_dpi)
                
                ax.plot(dates, analysis.kdj.k, label='K', alpha=0.8)
                ax.plot(dates, analysis.kdj.d, label='D', alpha=0.8)
                ax.plot(dates, analysis.kdj.j, label='J', alpha=0.8)
                
                ax.axhline(y=80, color='r', linestyle='--', alpha=0.5, label='超买线(80)')
                ax.axhline(y=20, color='g', linestyle='--', alpha=0.5, label='超卖线(20)')
                
                ax.set_title(f"{analysis.stock_name}({analysis.stock_code}) KDJ指标")
                ax.set_ylabel('KDJ')
                ax.grid(True, alpha=0.3)
                ax.legend()
                
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
                
                plt.tight_layout()
                
                kdj_chart_path = os.path.join(self.report_dir, f"{analysis.stock_code}_kdj_chart.png")
                plt.savefig(kdj_chart_path, dpi=self.config.chart_dpi, bbox_inches='tight')
                plt.close()
                
                chart_paths.append({
                    'type': 'kdj',
                    'path': kdj_chart_path,
                    'title': 'KDJ指标图'
                })
            
            self.logger.info(f"生成图表完成: {len(chart_paths)}个")
            
        except Exception as e:
            self.logger.error(f"生成图表失败: {str(e)}")
        
        return chart_paths
    
    def generate_html_report(self, analysis: ComprehensiveAnalysis) -> Tuple[bool, str, Optional[str]]:
        if not self.config.enable_html_report:
            return False, "HTML报告未启用", None
        
        try:
            chart_paths = self._generate_chart_paths(analysis)
            
            html_content = self._generate_html_content(analysis, chart_paths)
            
            html_path = os.path.join(self.report_dir, f"{analysis.stock_code}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"HTML报告生成成功: {html_path}")
            return True, "HTML报告生成成功", html_path
            
        except Exception as e:
            self.logger.error(f"HTML报告生成失败: {str(e)}")
            return False, str(e), None
    
    def _generate_html_content(self, analysis: ComprehensiveAnalysis, chart_paths: List[Dict[str, Any]]) -> str:
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{analysis.stock_name}({analysis.stock_code}) 技术分析报告</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; margin-bottom: 30px; }}
        h2 {{ color: #555; border-bottom: 2px solid #ddd; padding-bottom: 10px; margin-top: 30px; }}
        h3 {{ color: #666; margin-top: 20px; }}
        .summary {{ background-color: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .recommendation {{ font-size: 24px; font-weight: bold; color: #1976d2; margin: 20px 0; }}
        .confidence {{ font-size: 18px; color: #666; margin: 10px 0; }}
        .risk-level {{ display: inline-block; padding: 5px 15px; border-radius: 15px; margin: 10px 0; }}
        .risk-low {{ background-color: #4caf50; color: white; }}
        .risk-medium {{ background-color: #ff9800; color: white; }}
        .risk-high {{ background-color: #f44336; color: white; }}
        .key-points {{ margin: 20px 0; }}
        .key-points ul {{ list-style-type: none; padding: 0; }}
        .key-points li {{ background-color: #f9f9f9; padding: 10px; margin: 5px 0; border-left: 4px solid #2196f3; }}
        .warnings {{ background-color: #ffebee; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .warnings ul {{ list-style-type: none; padding: 0; }}
        .warnings li {{ padding: 10px; margin: 5px 0; border-left: 4px solid #f44336; }}
        .charts {{ margin: 30px 0; }}
        .charts img {{ max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .agent-analysis {{ margin: 20px 0; }}
        .agent-analysis .agent {{ background-color: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 8px; }}
        .agent-analysis .agent-name {{ font-weight: bold; color: #333; }}
        .agent-analysis .agent-recommendation {{ color: #1976d2; font-weight: bold; margin: 5px 0; }}
        .agent-analysis .agent-confidence {{ color: #666; }}
        .generated-at {{ text-align: right; color: #999; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{analysis.stock_name}({analysis.stock_code}) 技术分析报告</h1>
        <div class="generated-at">报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        
        <div class="summary">
            <h2>分析摘要</h2>
            <div class="recommendation">综合建议: {analysis.overall_recommendation}</div>
            <div class="confidence">综合置信度: {analysis.overall_confidence:.2f}</div>
            <div class="risk-level risk-{analysis.overall_risk_level}">风险等级: {analysis.overall_risk_level}</div>
        </div>
        
        <div class="key-points">
            <h2>关键点</h2>
            <ul>
"""
        
        for point in analysis.key_points:
            html += f"                <li>{point}</li>\n"
        
        html += """            </ul>
        </div>
        
        <div class="warnings">
            <h2>风险提示</h2>
            <ul>
"""
        
        for warning in analysis.warnings:
            html += f"                <li>{warning}</li>\n"
        
        html += """            </ul>
        </div>
        
        <div class="agent-analysis">
            <h2>Agent分析结果</h2>
"""
        
        for agent_analysis in analysis.agent_analyses:
            html += f"""            <div class="agent">
                <div class="agent-name">{agent_analysis.agent_name} ({agent_analysis.agent_type})</div>
                <div class="agent-recommendation">建议: {agent_analysis.recommendation}</div>
                <div class="agent-confidence">置信度: {agent_analysis.confidence:.2f} | 风险等级: {agent_analysis.risk_level}</div>
                <div>{agent_analysis.reasoning}</div>
            </div>
"""
        
        html += """        </div>
        
        <div class="charts">
            <h2>图表</h2>
"""
        
        for chart in chart_paths:
            html += f"""            <div>
                <h3>{chart['title']}</h3>
                <img src="{chart['path']}" alt="{chart['title']}">
            </div>
"""
        
        html += """        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def generate_json_report(self, analysis: ComprehensiveAnalysis) -> Tuple[bool, str, Optional[str]]:
        if not self.config.enable_json_report:
            return False, "JSON报告未启用", None
        
        try:
            report = AnalysisReport(
                stock_code=analysis.stock_code,
                stock_name=analysis.stock_name,
                report_date=analysis.analysis_date,
                summary=f"综合建议: {analysis.overall_recommendation}，置信度: {analysis.overall_confidence:.2f}，风险等级: {analysis.overall_risk_level}",
                technical_analysis=self._generate_technical_analysis_text(analysis),
                pattern_analysis=self._generate_pattern_analysis_text(analysis),
                volume_price_analysis=self._generate_volume_price_analysis_text(analysis),
                key_indicators=self._extract_key_indicators(analysis),
                recommendations=self._generate_recommendations(analysis),
                risk_warnings=analysis.warnings,
                charts=self._generate_chart_paths(analysis)
            )
            
            json_path = os.path.join(self.report_dir, f"{analysis.stock_code}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(report.model_dump(), f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"JSON报告生成成功: {json_path}")
            return True, "JSON报告生成成功", json_path
            
        except Exception as e:
            self.logger.error(f"JSON报告生成失败: {str(e)}")
            return False, str(e), None
    
    def _generate_technical_analysis_text(self, analysis: ComprehensiveAnalysis) -> str:
        parts = []
        
        if analysis.macd:
            parts.append(f"MACD: {analysis.macd.description}")
        
        if analysis.rsi:
            parts.append(f"RSI: {analysis.rsi.description}")
        
        if analysis.kdj:
            parts.append(f"KDJ: {analysis.kdj.description}")
        
        return "；".join(parts) if parts else "无技术指标数据"
    
    def _generate_pattern_analysis_text(self, analysis: ComprehensiveAnalysis) -> str:
        if not analysis.patterns:
            return "未检测到明显形态"
        
        patterns_info = []
        for pattern in analysis.patterns[:5]:
            patterns_info.append(f"{pattern.pattern_name}: {pattern.description}，置信度: {pattern.confidence:.2f}")
        
        return "；".join(patterns_info)
    
    def _generate_volume_price_analysis_text(self, analysis: ComprehensiveAnalysis) -> str:
        if not analysis.volume_price_relations:
            return "无量价关系数据"
        
        recent_relation = analysis.volume_price_relations[-1] if analysis.volume_price_relations else None
        if recent_relation:
            return f"最新量价关系: {recent_relation.relation_type}，{recent_relation.description}"
        
        return "无量价关系数据"
    
    def _extract_key_indicators(self, analysis: ComprehensiveAnalysis) -> Dict[str, Any]:
        indicators = {}
        
        if analysis.macd:
            indicators['MACD_DIF'] = analysis.macd.dif[-1] if analysis.macd.dif else None
            indicators['MACD_DEA'] = analysis.macd.dea[-1] if analysis.macd.dea else None
            indicators['MACD'] = analysis.macd.macd[-1] if analysis.macd.macd else None
        
        if analysis.rsi:
            indicators['RSI6'] = analysis.rsi.rsi6[-1] if analysis.rsi.rsi6 else None
            indicators['RSI12'] = analysis.rsi.rsi12[-1] if analysis.rsi.rsi12 else None
            indicators['RSI24'] = analysis.rsi.rsi24[-1] if analysis.rsi.rsi24 else None
        
        if analysis.kdj:
            indicators['KDJ_K'] = analysis.kdj.k[-1] if analysis.kdj.k else None
            indicators['KDJ_D'] = analysis.kdj.d[-1] if analysis.kdj.d else None
            indicators['KDJ_J'] = analysis.kdj.j[-1] if analysis.kdj.j else None
        
        return indicators
    
    def _generate_recommendations(self, analysis: ComprehensiveAnalysis) -> List[str]:
        recommendations = []
        
        recommendations.append(f"综合建议: {analysis.overall_recommendation}")
        
        if analysis.overall_recommendation == "买入":
            recommendations.append("建议逢低买入，注意控制仓位")
        elif analysis.overall_recommendation == "卖出":
            recommendations.append("建议逢高减仓，注意风险控制")
        elif analysis.overall_recommendation == "持有":
            recommendations.append("建议观望等待，关注关键点位")
        
        if analysis.overall_confidence > 0.7:
            recommendations.append("分析置信度较高，可参考执行")
        elif analysis.overall_confidence < 0.5:
            recommendations.append("分析置信度较低，建议谨慎决策")
        
        return recommendations
    
    def generate_pdf_report(self, analysis: ComprehensiveAnalysis) -> Tuple[bool, str, Optional[str]]:
        if not self.config.enable_pdf_report:
            return False, "PDF报告未启用", None
        
        try:
            try:
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.enums import TA_CENTER, TA_LEFT
                from reportlab.lib import colors
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                
                pdfmetrics.registerFont(TTFont('SimHei', 'SimHei.ttf'))
                
            except ImportError:
                self.logger.error("未安装reportlab库，请运行: pip install reportlab")
                return False, "PDF报告需要reportlab库", None
            
            pdf_path = os.path.join(self.report_dir, f"{analysis.stock_code}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
            
            doc = SimpleDocTemplate(pdf_path, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName='SimHei',
                fontSize=18,
                spaceAfter=20,
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontName='SimHei',
                fontSize=14,
                spaceAfter=10,
                spaceBefore=20
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName='SimHei',
                fontSize=10,
                spaceAfter=10
            )
            
            story.append(Paragraph(f"{analysis.stock_name}({analysis.stock_code}) 技术分析报告", title_style))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
            
            story.append(Spacer(1, 12))
            story.append(Paragraph("分析摘要", heading_style))
            story.append(Paragraph(f"综合建议: {analysis.overall_recommendation}", normal_style))
            story.append(Paragraph(f"综合置信度: {analysis.overall_confidence:.2f}", normal_style))
            story.append(Paragraph(f"风险等级: {analysis.overall_risk_level}", normal_style))
            
            story.append(Spacer(1, 12))
            story.append(Paragraph("关键点", heading_style))
            for point in analysis.key_points:
                story.append(Paragraph(f"• {point}", normal_style))
            
            story.append(Spacer(1, 12))
            story.append(Paragraph("风险提示", heading_style))
            for warning in analysis.warnings:
                story.append(Paragraph(f"• {warning}", normal_style))
            
            story.append(Spacer(1, 12))
            story.append(Paragraph("Agent分析结果", heading_style))
            for agent_analysis in analysis.agent_analyses:
                story.append(Paragraph(f"{agent_analysis.agent_name}:", normal_style))
                story.append(Paragraph(f"  建议: {agent_analysis.recommendation}", normal_style))
                story.append(Paragraph(f"  置信度: {agent_analysis.confidence:.2f}", normal_style))
                story.append(Paragraph(f"  风险等级: {agent_analysis.risk_level}", normal_style))
            
            doc.build(story)
            
            self.logger.info(f"PDF报告生成成功: {pdf_path}")
            return True, "PDF报告生成成功", pdf_path
            
        except Exception as e:
            self.logger.error(f"PDF报告生成失败: {str(e)}")
            return False, str(e), None
    
    def generate_all_reports(self, analysis: ComprehensiveAnalysis) -> Dict[str, str]:
        reports = {}
        
        success, msg, html_path = self.generate_html_report(analysis)
        if success and html_path:
            reports['html'] = html_path
        
        success, msg, json_path = self.generate_json_report(analysis)
        if success and json_path:
            reports['json'] = json_path
        
        success, msg, pdf_path = self.generate_pdf_report(analysis)
        if success and pdf_path:
            reports['pdf'] = pdf_path
        
        return reports
