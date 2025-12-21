from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from seer.logger import logger


class XiaohongshuAnalyzer:
    """
    Xiaohongshu data analyzer class
    Responsible for analyzing cleaned data and generating insights
    """
    
    def __init__(self):
        """
        Initialize the analyzer
        """
        self.logger = logger
    
    def analyze_notes(self, notes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze note data
        
        :param notes: List of cleaned note data
        :return: Analysis results
        """
        if not notes:
            return {"error": "No notes to analyze"}
        
        try:
            df = pd.DataFrame(notes)
            
            # Basic statistics
            stats = {
                "total_notes": len(df),
                "avg_likes": float(df["likes"].mean()),
                "avg_comments": float(df["comments"].mean()),
                "avg_collections": float(df["collections"].mean()),
                "avg_shares": float(df["shares"].mean()),
                "max_likes": int(df["likes"].max()),
                "max_comments": int(df["comments"].max()),
                "max_collections": int(df["collections"].max()),
                "max_shares": int(df["shares"].max()),
                "total_likes": int(df["likes"].sum()),
                "total_comments": int(df["comments"].sum()),
                "total_collections": int(df["collections"].sum()),
                "total_shares": int(df["shares"].sum()),
            }
            
            # Engagement rates
            stats.update({
                "avg_engagement_rate": float((df["likes"] + df["comments"] + df["collections"]).mean() / max(1, len(df))),
                "avg_comment_rate": float(df["comments"].mean() / max(1, df["likes"].mean())),
                "avg_collection_rate": float(df["collections"].mean() / max(1, df["likes"].mean())),
            })
            
            # Top performing notes
            top_notes = self._get_top_notes(df, 10)
            
            # Tag analysis
            tag_analysis = self._analyze_tags(notes)
            
            # Time analysis
            time_analysis = self._analyze_time_trends(notes)
            
            # Type distribution
            type_distribution = df["type"].value_counts().to_dict()
            
            return {
                "basic_stats": stats,
                "top_notes": top_notes,
                "tag_analysis": tag_analysis,
                "time_analysis": time_analysis,
                "type_distribution": type_distribution,
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing notes: {str(e)}")
            return {"error": str(e)}
    
    def analyze_users(self, users: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze user data
        
        :param users: List of cleaned user data
        :return: Analysis results
        """
        if not users:
            return {"error": "No users to analyze"}
        
        try:
            df = pd.DataFrame(users)
            
            # Basic statistics
            stats = {
                "total_users": len(df),
                "avg_followers": float(df["followers"].mean()),
                "avg_following": float(df["following"].mean()),
                "avg_notes": float(df["notes"].mean()),
                "avg_likes": float(df["likes"].mean()),
                "max_followers": int(df["followers"].max()),
                "max_following": int(df["following"].max()),
                "max_notes": int(df["notes"].max()),
                "max_likes": int(df["likes"].max()),
                "total_followers": int(df["followers"].sum()),
                "total_following": int(df["following"].sum()),
                "total_notes": int(df["notes"].sum()),
                "total_likes": int(df["likes"].sum()),
            }
            
            # Top users
            top_users = self._get_top_users(df, 10)
            
            # User level analysis
            level_analysis = df["level"].value_counts().to_dict()
            
            # Follower-following ratio
            df["follower_following_ratio"] = df["followers"] / (df["following"] + 1)  # Avoid division by zero
            avg_ratio = float(df["follower_following_ratio"].mean())
            
            return {
                "basic_stats": stats,
                "top_users": top_users,
                "level_analysis": level_analysis,
                "avg_follower_following_ratio": avg_ratio,
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing users: {str(e)}")
            return {"error": str(e)}
    
    def analyze_comments(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze comment data
        
        :param comments: List of cleaned comment data
        :return: Analysis results
        """
        if not comments:
            return {"error": "No comments to analyze"}
        
        try:
            df = pd.DataFrame(comments)
            
            # Basic statistics
            stats = {
                "total_comments": len(df),
                "avg_likes_per_comment": float(df["likes"].mean()),
                "max_likes_per_comment": int(df["likes"].max()),
                "total_likes_on_comments": int(df["likes"].sum()),
                "unique_users": df["user_id"].nunique(),
            }
            
            # Top commenters
            top_commenters = df["user_id"].value_counts().head(10).to_dict()
            
            # Comment time trends
            time_analysis = self._analyze_comment_time_trends(comments)
            
            return {
                "basic_stats": stats,
                "top_commenters": top_commenters,
                "time_analysis": time_analysis,
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing comments: {str(e)}")
            return {"error": str(e)}
    
    def generate_comprehensive_report(self, notes: List[Dict[str, Any]], users: List[Dict[str, Any]], comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive analysis report
        
        :param notes: List of cleaned note data
        :param users: List of cleaned user data
        :param comments: List of cleaned comment data
        :return: Comprehensive analysis report
        """
        return {
            "notes_analysis": self.analyze_notes(notes),
            "users_analysis": self.analyze_users(users),
            "comments_analysis": self.analyze_comments(comments),
            "report_generated_at": datetime.now().isoformat(),
        }
    
    # Private analysis methods
    def _get_top_notes(self, df: pd.DataFrame, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top performing notes based on engagement
        """
        # Calculate engagement score
        df["engagement_score"] = df["likes"] + df["comments"] * 2 + df["collections"] * 3
        
        # Sort by engagement score
        top_df = df.sort_values(by="engagement_score", ascending=False).head(limit)
        
        # Convert to list of dicts
        return top_df[["note_id", "title", "likes", "comments", "collections", "engagement_score"]].to_dict("records")
    
    def _get_top_users(self, df: pd.DataFrame, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top users based on followers
        """
        top_df = df.sort_values(by="followers", ascending=False).head(limit)
        return top_df[["user_id", "name", "followers", "following", "notes", "likes"]].to_dict("records")
    
    def _analyze_tags(self, notes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze tags from notes
        """
        tag_counts = {}
        tag_engagement = {}
        
        for note in notes:
            tags = note.get("tags", [])
            engagement = note["likes"] + note["comments"] + note["collections"]
            
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                tag_engagement[tag] = tag_engagement.get(tag, 0) + engagement
        
        # Calculate average engagement per tag
        tag_avg_engagement = {
            tag: engagement / count for tag, count in tag_counts.items()
            for engagement in [tag_engagement[tag]]
        }
        
        # Sort tags
        top_tags_by_count = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        top_tags_by_engagement = sorted(tag_avg_engagement.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return {
            "total_unique_tags": len(tag_counts),
            "top_tags_by_count": [{
                "tag": tag,
                "count": count
            } for tag, count in top_tags_by_count],
            "top_tags_by_engagement": [{
                "tag": tag,
                "avg_engagement": float(engagement)
            } for tag, engagement in top_tags_by_engagement],
        }
    
    def _analyze_time_trends(self, notes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze time trends
        """
        # Filter notes with valid create_time
        valid_notes = [note for note in notes if note.get("create_time")]
        if not valid_notes:
            return {"error": "No valid time data"}
        
        df = pd.DataFrame(valid_notes)
        df["create_time"] = pd.to_datetime(df["create_time"])
        
        # Daily distribution
        daily_dist = df.resample('D', on='create_time').size().to_dict()
        daily_dist = {str(date.date()): count for date, count in daily_dist.items()}
        
        # Hourly distribution
        hourly_dist = df["create_time"].dt.hour.value_counts().sort_index().to_dict()
        
        # Engagement by hour
        df["hour"] = df["create_time"].dt.hour
        hourly_engagement = df.groupby("hour")["likes", "comments", "collections"].mean().to_dict()
        
        return {
            "daily_distribution": daily_dist,
            "hourly_distribution": hourly_dist,
            "hourly_engagement": hourly_engagement,
        }
    
    def _analyze_comment_time_trends(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze comment time trends
        """
        # Filter comments with valid create_time
        valid_comments = [comment for comment in comments if comment.get("create_time")]
        if not valid_comments:
            return {"error": "No valid time data"}
        
        df = pd.DataFrame(valid_comments)
        df["create_time"] = pd.to_datetime(df["create_time"])
        
        # Daily distribution
        daily_dist = df.resample('D', on='create_time').size().to_dict()
        daily_dist = {str(date.date()): count for date, count in daily_dist.items()}
        
        # Hourly distribution
        hourly_dist = df["create_time"].dt.hour.value_counts().sort_index().to_dict()
        
        return {
            "daily_distribution": daily_dist,
            "hourly_distribution": hourly_dist,
        }
    
    def calculate_correlations(self, notes: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate correlations between engagement metrics
        """
        if not notes:
            return {}
        
        try:
            df = pd.DataFrame(notes)
            
            # Calculate correlation matrix
            corr_matrix = df[["likes", "comments", "collections", "shares"]].corr()
            
            # Flatten the matrix to a dict
            correlations = {}
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    col1 = corr_matrix.columns[i]
                    col2 = corr_matrix.columns[j]
                    correlations[f"{col1}_vs_{col2}"] = float(corr_matrix.iloc[i, j])
            
            return correlations
            
        except Exception as e:
            self.logger.error(f"Error calculating correlations: {str(e)}")
            return {}
    
    def identify_trending_topics(self, notes: List[Dict[str, Any]], days: int = 7) -> List[Dict[str, Any]]:
        """
        Identify trending topics based on recent notes
        """
        if not notes:
            return []
        
        try:
            df = pd.DataFrame(notes)
            df["create_time"] = pd.to_datetime(df["create_time"])
            
            # Filter notes from the last N days
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_df = df[df["create_time"] >= cutoff_date]
            
            if len(recent_df) == 0:
                return []
            
            # Extract hashtags
            hashtags = []
            for _, note in recent_df.iterrows():
                hashtags.extend(note.get("hashtags", []))
            
            # Count hashtag frequency
            from collections import Counter
            hashtag_counts = Counter(hashtags)
            
            # Get top trending hashtags
            top_hashtags = hashtag_counts.most_common(20)
            
            return [{
                "hashtag": hashtag,
                "count": count
            } for hashtag, count in top_hashtags]
            
        except Exception as e:
            self.logger.error(f"Error identifying trending topics: {str(e)}")
            return []
