from typing import List, Dict, Any, Optional
from openai import OpenAI
from seer.logger import logger


class EmbeddingModel:
    def __init__(self, api_key: Optional[str] = None, 
                 base_url: Optional[str] = None,
                 model: str = "text-embedding-3-small"):
        self.model = model
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        logger.info(f"初始化嵌入模型: {model}")
    
    def get_embedding(self, text: str) -> List[float]:
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"获取嵌入向量失败: {str(e)}")
            raise
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            embeddings = []
            for text in texts:
                embedding = self.get_embedding(text)
                embeddings.append(embedding)
            return embeddings
        except Exception as e:
            logger.error(f"批量获取嵌入向量失败: {str(e)}")
            raise
