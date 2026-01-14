from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import re
import json
import hashlib
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from seer.logger import logger


class VectorStore:
    def __init__(self, collection_name: str = "seer_knowledge", 
                 vector_size: int = 1536,
                 url: str = "http://localhost:6333",
                 use_memory: bool = False,
                 cache_dir: str = "d:/code/seer/data/primary_thinking/vector"):
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.use_memory = use_memory
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            if use_memory:
                self.client = QdrantClient(":memory:")
                logger.info("使用内存模式 Qdrant")
            else:
                self.client = QdrantClient(url=url)
                logger.info(f"连接 Qdrant: {url}")
            
            self._ensure_collection()
        except Exception as e:
            logger.warning(f"连接 Qdrant 失败: {str(e)}，切换到内存模式")
            self.client = QdrantClient(":memory:")
            self.use_memory = True
            self._ensure_collection()
    
    def _ensure_collection(self):
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"创建 Qdrant 集合: {self.collection_name}")
            else:
                logger.info(f"Qdrant 集合已存在: {self.collection_name}")
        except Exception as e:
            logger.error(f"确保集合存在失败: {str(e)}")
            raise
    
    def _compute_document_hash(self, documents: List[Dict[str, Any]]) -> str:
        content_hash = hashlib.md5()
        for doc in sorted(documents, key=lambda x: x['id']):
            content_hash.update(doc['content'].encode('utf-8'))
        return content_hash.hexdigest()
    
    def _get_cache_path(self, hash_value: str) -> Path:
        return self.cache_dir / f"{hash_value}.json"
    
    def _load_vectors_from_cache(self, hash_value: str) -> Optional[List[List[float]]]:
        cache_path = self._get_cache_path(hash_value)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            logger.info(f"从缓存加载向量: {hash_value}")
            return cache_data.get('embeddings')
        except Exception as e:
            logger.warning(f"加载缓存失败: {str(e)}")
            return None
    
    def _save_vectors_to_cache(self, hash_value: str, embeddings: List[List[float]]):
        cache_path = self._get_cache_path(hash_value)
        
        try:
            cache_data = {
                'hash': hash_value,
                'embeddings': embeddings,
                'timestamp': str(Path(__file__).stat().st_mtime)
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"保存向量到缓存: {hash_value}")
        except Exception as e:
            logger.warning(f"保存缓存失败: {str(e)}")
    
    def load_documents_from_directory(self, directory_path: str, force_rebuild: bool = False) -> Tuple[List[Dict[str, Any]], Optional[List[List[float]]]]:
        documents = []
        directory = Path(directory_path)
        
        if not directory.exists():
            logger.error(f"目录不存在: {directory_path}")
            return [], None
        
        for file_path in sorted(directory.glob("*.md")):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                doc_id = file_path.stem
                documents.append({
                    "id": doc_id,
                    "content": content,
                    "file_path": str(file_path)
                })
                
                logger.info(f"加载文档: {doc_id}")
            except Exception as e:
                logger.error(f"加载文档失败 {file_path}: {str(e)}")
        
        logger.info(f"共加载 {len(documents)} 个文档")
        
        if not documents:
            return [], None
        
        doc_hash = self._compute_document_hash(documents)
        
        if not force_rebuild:
            cached_embeddings = self._load_vectors_from_cache(doc_hash)
            if cached_embeddings is not None:
                logger.info(f"使用缓存的向量，共 {len(cached_embeddings)} 个")
                return documents, cached_embeddings
        
        return documents, None
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        chunks = []
        sentences = re.split(r'[。！？\n]', text)
        
        current_chunk = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += sentence + "。"
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def add_documents(self, documents: List[Dict[str, Any]], 
                      embeddings: List[List[float]],
                      cache_embeddings: bool = True):
        points = []
        point_id = 0
        
        for doc in documents:
            chunks = self.chunk_text(doc["content"])
            
            for i, chunk in enumerate(chunks):
                if point_id < len(embeddings):
                    points.append(
                        PointStruct(
                            id=point_id,
                            vector=embeddings[point_id],
                            payload={
                                "content": chunk,
                                "doc_id": doc["id"],
                                "chunk_index": i,
                                "file_path": doc["file_path"]
                            }
                        )
                    )
                    point_id += 1
        
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"添加 {len(points)} 个向量点到集合")
            
            if cache_embeddings:
                doc_hash = self._compute_document_hash(documents)
                self._save_vectors_to_cache(doc_hash, embeddings)
    
    def build_vector_index(self, directory_path: str, embedding_model, force_rebuild: bool = False) -> bool:
        try:
            documents, cached_embeddings = self.load_documents_from_directory(directory_path, force_rebuild)
            
            if not documents:
                logger.warning("没有文档需要处理")
                return False
            
            if cached_embeddings is not None:
                self.add_documents(documents, cached_embeddings, cache_embeddings=False)
                return True
            
            all_chunks = []
            for doc in documents:
                chunks = self.chunk_text(doc["content"])
                all_chunks.extend(chunks)
            
            logger.info(f"共生成 {len(all_chunks)} 个文本块")
            
            embeddings = embedding_model.get_embeddings(all_chunks)
            
            self.add_documents(documents, embeddings, cache_embeddings=True)
            
            return True
            
        except Exception as e:
            logger.error(f"构建向量索引失败: {str(e)}")
            return False
    
    def search(self, query_embedding: List[float], 
               limit: int = 5,
               score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        try:
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=limit,
                score_threshold=score_threshold
            )
            
            search_results = []
            for result in results.points:
                search_results.append({
                    "content": result.payload["content"],
                    "doc_id": result.payload["doc_id"],
                    "chunk_index": result.payload["chunk_index"],
                    "score": result.score,
                    "file_path": result.payload["file_path"]
                })
            
            logger.info(f"搜索到 {len(search_results)} 个相关结果")
            return search_results
            
        except Exception as e:
            logger.error(f"搜索失败: {str(e)}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"获取集合信息失败: {str(e)}")
            return {}
    
    def delete_collection(self):
        try:
            self.client.delete_collection(self.collection_name)
            logger.info(f"删除集合: {self.collection_name}")
        except Exception as e:
            logger.error(f"删除集合失败: {str(e)}")
            raise
