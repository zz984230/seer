from typing import Dict, List, Any, Optional
import os
import json
import pandas as pd
from datetime import datetime
from seer.logger import logger


class XiaohongshuReporter:
    """
    Xiaohongshu analysis report generator
    Responsible for generating reports based on analysis results
    """
    
    def __init__(self, report_dir: str = "reports"):
        """
        Initialize the reporter
        
        :param report_dir: Directory to save reports
        """
        self.logger = logger
        self.report_dir = report_dir
        self.current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
    def generate_html_report(self, analysis_results: Dict[str, Any], report_title: str = "Xiaohongshu Analysis Report") -> Optional[str]:
        """
        Generate HTML report
        
        :param analysis_results: Analysis results from analyzer
        :param report_title: Title of the report
        :return: Path to generated HTML report or None if failed
        """
        try:
            # Create report directory
            report_path = os.path.join(self.report_dir, f"report_{self.current_date}")
            os.makedirs(report_path, exist_ok=True)
            
            # Create HTML content
            html_content = self._generate_html_content(analysis_results, report_title)
            
            # Write to file
            html_file_path = os.path.join(report_path, "report.html")
            with open(html_file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            self.logger.info(f"HTML report generated: {html_file_path}")
            return html_file_path
            
        except Exception as e:
            self.logger.error(f"Error generating HTML report: {str(e)}")
            return None
    
    def generate_excel_report(self, analysis_results: Dict[str, Any], file_name: str = "xiaohongshu_analysis.xlsx") -> Optional[str]:
        """
        Generate Excel report
        
        :param analysis_results: Analysis results from analyzer
        :param file_name: Name of the Excel file
        :return: Path to generated Excel file or None if failed
        """
        try:
            # Create report directory
            report_path = os.path.join(self.report_dir, f"report_{self.current_date}")
            os.makedirs(report_path, exist_ok=True)
            
            # Create Excel writer
            excel_file_path = os.path.join(report_path, file_name)
            with pd.ExcelWriter(excel_file_path, engine="xlsxwriter") as writer:
                # Basic statistics sheet
                self._write_basic_stats(analysis_results, writer)
                
                # Top notes sheet
                self._write_top_notes(analysis_results, writer)
                
                # Tag analysis sheet
                self._write_tag_analysis(analysis_results, writer)
                
                # Time trends sheet
                self._write_time_trends(analysis_results, writer)
            
            self.logger.info(f"Excel report generated: {excel_file_path}")
            return excel_file_path
            
        except Exception as e:
            self.logger.error(f"Error generating Excel report: {str(e)}")
            return None
    
    def generate_json_report(self, analysis_results: Dict[str, Any], file_name: str = "xiaohongshu_analysis.json") -> Optional[str]:
        """
        Generate JSON report
        
        :param analysis_results: Analysis results from analyzer
        :param file_name: Name of the JSON file
        :return: Path to generated JSON file or None if failed
        """
        try:
            # Create report directory
            report_path = os.path.join(self.report_dir, f"report_{self.current_date}")
            os.makedirs(report_path, exist_ok=True)
            
            # Write to file
            json_file_path = os.path.join(report_path, file_name)
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(analysis_results, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"JSON report generated: {json_file_path}")
            return json_file_path
            
        except Exception as e:
            self.logger.error(f"Error generating JSON report: {str(e)}")
            return None
    
    def generate_all_reports(self, analysis_results: Dict[str, Any], report_title: str = "Xiaohongshu Analysis Report") -> Dict[str, str]:
        """
        Generate all report formats
        
        :param analysis_results: Analysis results from analyzer
        :param report_title: Title of the report
        :return: Dictionary of generated report paths
        """
        reports = {}
        
        html_path = self.generate_html_report(analysis_results, report_title)
        if html_path:
            reports["html"] = html_path
        
        excel_path = self.generate_excel_report(analysis_results)
        if excel_path:
            reports["excel"] = excel_path
        
        json_path = self.generate_json_report(analysis_results)
        if json_path:
            reports["json"] = json_path
        
        return reports
    
    # Private methods for report generation
    def _generate_html_content(self, analysis_results: Dict[str, Any], report_title: str) -> str:
        """
        Generate HTML content for the report
        
        :param analysis_results: Analysis results from analyzer
        :param report_title: Title of the report
        :return: HTML content as string
        """
        # Basic HTML template
        html_template = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{report_title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #333; text-align: center; }}
                h2 {{ color: #555; border-bottom: 2px solid #ddd; padding-bottom: 10px; margin-top: 30px; }}
                h3 {{ color: #666; margin-top: 20px; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
                .stat-card {{ background-color: #f9f9f9; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: #333; }}
                .stat-label {{ font-size: 14px; color: #666; margin-top: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
                th {{ background-color: #f2f2f2; font-weight: bold; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .tag-cloud {{ margin: 20px 0; display: flex; flex-wrap: wrap; gap: 10px; }}
                .tag {{ background-color: #e3f2fd; padding: 5px 10px; border-radius: 15px; font-size: 14px; }}
                .tag.high {{ background-color: #bbdefb; font-size: 16px; }}
                .tag.medium {{ background-color: #e3f2fd; font-size: 14px; }}
                .tag.low {{ background-color: #f3e5f5; font-size: 12px; }}
                .generated-at {{ text-align: right; color: #999; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{report_title}</h1>
                <div class="generated-at">报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
        """
        
        # Notes analysis section
        if "notes_analysis" in analysis_results and "error" not in analysis_results["notes_analysis"]:
            html_template += """
                <h2>笔记分析</h2>
                <h3>基础统计</h3>
                <div class="stats-grid">
            """
            
            stats = analysis_results["notes_analysis"]["basic_stats"]
            for key, value in stats.items():
                # Skip some detailed stats for better readability
                if key in ["total_notes", "avg_likes", "avg_comments", "avg_collections", "avg_shares", "avg_engagement_rate"]:
                    label = self._get_stat_label(key)
                    html_template += f"""
                        <div class="stat-card">
                            <div class="stat-value">{value:.2f}</div>
                            <div class="stat-label">{label}</div>
                        </div>
                    """
            
            html_template += """
                </div>
                <h3>热门笔记</h3>
                <table>
                    <tr>
                        <th>排名</th>
                        <th>标题</th>
                        <th>点赞数</th>
                        <th>评论数</th>
                        <th>收藏数</th>
                    </tr>
            """
            
            for i, note in enumerate(analysis_results["notes_analysis"]["top_notes"], 1):
                html_template += f"""
                    <tr>
                        <td>{i}</td>
                        <td>{note['title']}</td>
                        <td>{note['likes']}</td>
                        <td>{note['comments']}</td>
                        <td>{note['collections']}</td>
                    </tr>
                """
            
            html_template += """
                </table>
            """
            
            # Tag analysis
            if "tag_analysis" in analysis_results["notes_analysis"]:
                html_template += """
                    <h3>标签分析</h3>
                    <div class="tag-cloud">
                """
                
                for tag_info in analysis_results["notes_analysis"]["tag_analysis"]["top_tags_by_count"][:20]:
                    html_template += f"<span class='tag high'>{tag_info['tag']} ({tag_info['count']})</span>"
                
                html_template += "</div>"
        
        # Users analysis section
        if "users_analysis" in analysis_results and "error" not in analysis_results["users_analysis"]:
            html_template += """
                <h2>用户分析</h2>
                <h3>基础统计</h3>
                <div class="stats-grid">
            """
            
            stats = analysis_results["users_analysis"]["basic_stats"]
            for key, value in stats.items():
                if key in ["total_users", "avg_followers", "avg_following", "avg_notes", "avg_likes"]:
                    label = self._get_stat_label(key)
                    html_template += f"""
                        <div class="stat-card">
                            <div class="stat-value">{value:.2f}</div>
                            <div class="stat-label">{label}</div>
                        </div>
                    """
            
            html_template += "</div>"
        
        # Comments analysis section
        if "comments_analysis" in analysis_results and "error" not in analysis_results["comments_analysis"]:
            html_template += """
                <h2>评论分析</h2>
                <h3>基础统计</h3>
                <div class="stats-grid">
            """
            
            stats = analysis_results["comments_analysis"]["basic_stats"]
            for key, value in stats.items():
                if key in ["total_comments", "avg_likes_per_comment", "unique_users"]:
                    label = self._get_stat_label(key)
                    html_template += f"""
                        <div class="stat-card">
                            <div class="stat-value">{value:.2f}</div>
                            <div class="stat-label">{label}</div>
                        </div>
                    """
            
            html_template += "</div>"
        
        # Close HTML
        html_template += """
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def _write_basic_stats(self, analysis_results: Dict[str, Any], writer: pd.ExcelWriter):
        """
        Write basic statistics to Excel
        """
        # Create stats dictionary
        stats_dict = {}
        
        if "notes_analysis" in analysis_results and "error" not in analysis_results["notes_analysis"]:
            stats_dict["笔记统计"] = analysis_results["notes_analysis"]["basic_stats"]
        
        if "users_analysis" in analysis_results and "error" not in analysis_results["users_analysis"]:
            stats_dict["用户统计"] = analysis_results["users_analysis"]["basic_stats"]
        
        if "comments_analysis" in analysis_results and "error" not in analysis_results["comments_analysis"]:
            stats_dict["评论统计"] = analysis_results["comments_analysis"]["basic_stats"]
        
        # Write to Excel
        for sheet_name, stats in stats_dict.items():
            df = pd.DataFrame.from_dict(stats, orient="index", columns=["数值"])
            df.to_excel(writer, sheet_name=sheet_name, index_label="指标")
    
    def _write_top_notes(self, analysis_results: Dict[str, Any], writer: pd.ExcelWriter):
        """
        Write top notes to Excel
        """
        if "notes_analysis" in analysis_results and "error" not in analysis_results["notes_analysis"]:
            top_notes = analysis_results["notes_analysis"]["top_notes"]
            if top_notes:
                df = pd.DataFrame(top_notes)
                df.to_excel(writer, sheet_name="热门笔记", index=False)
    
    def _write_tag_analysis(self, analysis_results: Dict[str, Any], writer: pd.ExcelWriter):
        """
        Write tag analysis to Excel
        """
        if "notes_analysis" in analysis_results and "error" not in analysis_results["notes_analysis"] and "tag_analysis" in analysis_results["notes_analysis"]:
            tag_analysis = analysis_results["notes_analysis"]["tag_analysis"]
            
            if "top_tags_by_count" in tag_analysis:
                df_count = pd.DataFrame(tag_analysis["top_tags_by_count"])
                df_count.to_excel(writer, sheet_name="标签统计", index=False)
            
            if "top_tags_by_engagement" in tag_analysis:
                df_engagement = pd.DataFrame(tag_analysis["top_tags_by_engagement"])
                df_engagement.to_excel(writer, sheet_name="标签互动", index=False)
    
    def _write_time_trends(self, analysis_results: Dict[str, Any], writer: pd.ExcelWriter):
        """
        Write time trends to Excel
        """
        if "notes_analysis" in analysis_results and "error" not in analysis_results["notes_analysis"] and "time_analysis" in analysis_results["notes_analysis"]:
            time_analysis = analysis_results["notes_analysis"]["time_analysis"]
            
            if "daily_distribution" in time_analysis:
                df_daily = pd.DataFrame.from_dict(time_analysis["daily_distribution"], orient="index", columns=["笔记数量"])
                df_daily.to_excel(writer, sheet_name="每日分布", index_label="日期")
            
            if "hourly_distribution" in time_analysis:
                df_hourly = pd.DataFrame.from_dict(time_analysis["hourly_distribution"], orient="index", columns=["笔记数量"])
                df_hourly.to_excel(writer, sheet_name="每小时分布", index_label="小时")
    
    def _get_stat_label(self, stat_key: str) -> str:
        """
        Get human-readable label for stat key
        """
        labels = {
            "total_notes": "总笔记数",
            "avg_likes": "平均点赞数",
            "avg_comments": "平均评论数",
            "avg_collections": "平均收藏数",
            "avg_shares": "平均分享数",
            "avg_engagement_rate": "平均互动率",
            "total_users": "总用户数",
            "avg_followers": "平均粉丝数",
            "avg_following": "平均关注数",
            "avg_notes": "平均笔记数",
            "total_comments": "总评论数",
            "avg_likes_per_comment": "平均评论点赞数",
            "unique_users": "独立评论用户数",
        }
        return labels.get(stat_key, stat_key)
