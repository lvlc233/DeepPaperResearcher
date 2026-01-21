'''
开发者: BackendAgent
当前版本: v1.1_embedding_service
创建时间: 2026年01月08日 15:30
更新时间: 2026年01月09日 16:20
更新记录:
    [2026年01月08日 15:30:v1.0_embedding_service:创建文本向量化服务，支持OpenAI和Ollama模型]
    [2026年01月09日 16:20:v1.1_embedding_service:新增本地ONNX模型(BGE-M3)支持及SiliconFlow云端回退机制]
'''

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

import numpy as np
from openai import AsyncOpenAI

from base.config import settings

from loguru import logger


class BaseEmbeddingModel(ABC):
    """文本嵌入模型基类"""

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """嵌入单个文本"""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文本"""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """嵌入维度"""
        pass

# 定义数据模型
class OpenAIEmbeddingModel(BaseEmbeddingModel):
    """OpenAI兼容接口的文本嵌入模型 (支持OpenAI, SiliconFlow等)"""

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: Optional[str] = None
    ):
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        logger.info(f"OpenAI兼容嵌入模型初始化完成: {model}, base_url={base_url}")

    async def embed_text(self, text: str) -> List[float]:
        """嵌入单个文本"""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI文本嵌入失败: {e}")
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文本"""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            # 保证返回顺序与输入一致
            embeddings = [None] * len(texts)
            for data in response.data:
                embeddings[data.index] = data.embedding
            return embeddings
        except Exception as e:
            logger.error(f"OpenAI批量嵌入失败: {e}")
            raise

    @property
    def dimension(self) -> int:
        """嵌入维度"""
        # BGE-M3: 1024, OpenAI Small: 1536, Qwen-Embedding: 1024?
        # Qwen/Qwen3-Embedding-0.6B dimension is typically 1024 or 1536. 
        # Checking online: Qwen-Embedding is likely 1024.
        # But text-embedding-ada-002 is 1536.
        # For safety, we can make this configurable or query the model. 
        # For now, return 1536 as a safe default for vector DB compatibility if not specified.
        # Ideally, we should check the model config.
        if "bge-m3" in self.model.lower():
            return 1024
        return 1536 # Default for OpenAI

# 定义数据模型
class LocalOnnxEmbeddingModel(BaseEmbeddingModel):
    """本地ONNX嵌入模型 (BGE-M3)"""

    def __init__(self, model_path: str, tokenizer_path: Optional[str] = None):
        self.model_path = model_path
        self.tokenizer_path = tokenizer_path or os.path.join(model_path, "tokenizer.json")
        self._tokenizer = None
        self._session = None
        self._dimension = 1024 # BGE-M3 default

        self._load_model()

    def _load_model(self):
        try:
            import onnxruntime as ort
            from tokenizers import Tokenizer

            # 加载Tokenizer
            if os.path.exists(self.tokenizer_path):
                self._tokenizer = Tokenizer.from_file(self.tokenizer_path)
                # 启用截断和填充
                self._tokenizer.enable_truncation(max_length=8192)
                self._tokenizer.enable_padding(pad_id=0, pad_token="[PAD]", length=8192)
            else:
                logger.error(f"Tokenizer文件未找到: {self.tokenizer_path}")
                raise FileNotFoundError(f"Tokenizer not found at {self.tokenizer_path}")

            # 加载ONNX模型
            model_file = os.path.join(self.model_path, "model.onnx")
            if not os.path.exists(model_file):
                 # 尝试直接使用 model_path 如果它本身就是文件
                 if self.model_path.endswith(".onnx") and os.path.exists(self.model_path):
                     model_file = self.model_path
                 else:
                    logger.error(f"ONNX模型文件未找到: {model_file}")
                    raise FileNotFoundError(f"ONNX model not found at {model_file}")

            # 使用CPU
            providers = ['CPUExecutionProvider']
            self._session = ort.InferenceSession(model_file, providers=providers)
            
            logger.info(f"本地ONNX模型加载成功: {model_file}")

        except ImportError as e:
            logger.error(f"缺少必要的依赖库: {e}. 请安装 onnxruntime 和 tokenizers")
            raise
        except Exception as e:
            logger.error(f"本地模型加载失败: {e}")
            raise

    def _compute_embedding(self, text: str) -> List[float]:
        # Tokenization
        encoded = self._tokenizer.encode(text)
        
        input_ids = np.array([encoded.ids], dtype=np.int64)
        attention_mask = np.array([encoded.attention_mask], dtype=np.int64)
        # BGE-M3 ONNX inputs might vary, usually input_ids, attention_mask
        # Some models require token_type_ids
        
        inputs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask
        }
        
        # Check model inputs
        model_inputs = [x.name for x in self._session.get_inputs()]
        if "token_type_ids" in model_inputs:
             inputs["token_type_ids"] = np.array([encoded.type_ids], dtype=np.int64)

        # Inference
        outputs = self._session.run(None, inputs)
        
        # BGE-M3: use the first output (last_hidden_state), take CLS token (index 0)
        # Ensure normalization
        last_hidden_state = outputs[0] # [batch, seq_len, hidden_size]
        cls_embedding = last_hidden_state[0, 0, :]
        
        # Normalize
        norm = np.linalg.norm(cls_embedding)
        if norm > 0:
            cls_embedding = cls_embedding / norm
            
        return cls_embedding.tolist()

    async def embed_text(self, text: str) -> List[float]:
        """嵌入单个文本 (Run in executor to avoid blocking)"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._compute_embedding, text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文本"""
        # 简单实现：循环调用单个嵌入
        # 优化方向：真正实现batch inference
        # For now, parallelize the CPU calls
        loop = asyncio.get_running_loop()
        tasks = [loop.run_in_executor(None, self._compute_embedding, text) for text in texts]
        return await asyncio.gather(*tasks)

    @property
    def dimension(self) -> int:
        return self._dimension

# 唯一暴露,提供通用的向量化服务。
class EmbeddingService:
    """文本向量化服务 (支持本地/云端自动回退)"""

    def __init__(self):
        self.primary_model: Optional[BaseEmbeddingModel] = None
        self.fallback_model: Optional[BaseEmbeddingModel] = None
        self._init_models()

    def _init_models(self):
        # 1. 初始化 Primary Model (根据配置)
        try:
            if settings.embedding_type == "local":
                logger.info("尝试加载本地 Embedding 模型...")
                self.primary_model = LocalOnnxEmbeddingModel(
                    model_path=settings.local_embedding_model_path,
                    tokenizer_path=settings.local_embedding_tokenizer_path
                )
            elif settings.embedding_type == "siliconflow":
                self.primary_model = self._create_siliconflow_model()
            elif settings.embedding_type == "openai":
                self.primary_model = OpenAIEmbeddingModel(
                    model="text-embedding-ada-002",
                    api_key=settings.openai_api_key
                )
        except Exception as e:
            logger.error(f"主模型初始化失败: {e}, 尝试初始化回退模型")
            self.primary_model = None

        # 2. 初始化 Fallback Model (SiliconFlow)
        # 如果主模型不是 SiliconFlow，则配置 SiliconFlow 为回退
        if settings.embedding_type != "siliconflow":
            try:
                self.fallback_model = self._create_siliconflow_model()
                logger.info("SiliconFlow 回退模型初始化成功")
            except Exception as e:
                logger.warning(f"回退模型初始化失败: {e}")

    def _create_siliconflow_model(self) -> OpenAIEmbeddingModel:
        if not settings.siliconflow_api_key:
            raise ValueError("SiliconFlow API Key 未配置")
        return OpenAIEmbeddingModel(
            model=settings.siliconflow_embedding_model,
            api_key=settings.siliconflow_api_key,
            base_url=settings.siliconflow_base_url
        )

    async def embed_text(self, text: str) -> List[float]:
        """嵌入单个文本 (带回退机制)"""
        errors = []
        
        # 尝试主模型
        if self.primary_model:
            try:
                return await self.primary_model.embed_text(text)
            except Exception as e:
                logger.error(f"主模型调用失败: {e}")
                errors.append(str(e))
        
        # 尝试回退模型
        if self.fallback_model:
            logger.info("切换到回退模型 (SiliconFlow)...")
            try:
                return await self.fallback_model.embed_text(text)
            except Exception as e:
                logger.error(f"回退模型调用失败: {e}")
                errors.append(str(e))
        
        raise RuntimeError(f"所有嵌入模型均不可用: {'; '.join(errors)}")

    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 10
    ) -> List[List[float]]:
        """批量嵌入文本 (带回退机制)"""
        # 分批逻辑
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            try:
                batch_emb = await self._embed_batch_safe(batch)
                embeddings.extend(batch_emb)
            except Exception as e:
                logger.error(f"批次处理失败: {e}")
                # 再次尝试逐个处理或抛出
                raise
        return embeddings

    async def _embed_batch_safe(self, texts: List[str]) -> List[List[float]]:
        # 尝试主模型
        if self.primary_model:
            try:
                return await self.primary_model.embed_batch(texts)
            except Exception as e:
                logger.error(f"主模型批量调用失败: {e}")
        
        # 尝试回退模型
        if self.fallback_model:
            logger.info("切换到回退模型 (SiliconFlow)...")
            try:
                return await self.fallback_model.embed_batch(texts)
            except Exception as e:
                logger.error(f"回退模型批量调用失败: {e}")
        
        raise RuntimeError("所有嵌入模型均不可用")

# 辅助函数
async def embed_batch(texts: List[str], model_type: str = "auto") -> List[List[float]]:
    service = EmbeddingService()
    return await service.embed_batch(texts)
