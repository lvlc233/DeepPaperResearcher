'''
开发者: BackendAgent
当前版本: v1.3_config
创建时间: 2026年01月08日 11:30
更新时间: 2026年01月20日 10:35
更新记录:
    [2026年01月08日 11:30:v1.0_config:创建数据库配置模块]
    [2026年01月09日 15:45:v1.1_config:添加Embedding服务配置(本地ONNX/云端SiliconFlow)]
    [2026年01月16日 10:00:v1.2_config:修复transformers缓存路径警告]
    [2026年01月20日 10:35:v1.3_config:新增Refresh Token过期配置用于认证刷新]
'''

from typing import Optional, Literal


# pydantic v2 use pydantic_settings
# 考虑到兼容性，这里暂时假设是 v1 或已安装 pydantic-settings

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""

    # 数据库配置
    database_url: str = "postgresql://postgres:lixiaozai233@localhost:5432/dpra"

    # Redis配置
    redis_url: str = "redis://localhost:6379/0"

    # JWT配置
    jwt_secret_key: str = "your-secret-key-here"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 180
    jwt_refresh_expiration_days: int = 7

    # 文件上传配置
    upload_dir: str = "uploads"
    max_file_size: int = 50 * 1024 * 1024  # 50MB

    # AI模型配置
    openai_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"

    # Embedding 配置
    embedding_type: Literal["local", "siliconflow", "openai", "ollama"] = "local"
    
    # Local Embedding (ONNX)
    local_embedding_model_path: str = r"D:\模型\bge-m3-onnx\bge-m3-onnx"
    local_embedding_tokenizer_path: Optional[str] = None # 默认为 model_path
    
    # SiliconFlow Embedding
    siliconflow_api_key: Optional[str] = None
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1"
    siliconflow_embedding_model: str = "Qwen/Qwen3-Embedding-0.6B"

    # 异步任务配置
    arq_redis_url: str = "redis://localhost:6379/1"

    # Neo4j配置
    neo4j_url: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # 日志配置
    log_level: str = "INFO"

    # class Config:
    #     env_file = ".env"
    #     env_file_encoding = "utf-8"


# 创建全局配置实例
settings = Settings()
