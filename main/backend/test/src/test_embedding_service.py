
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from base.embedding.embedding_service import EmbeddingService, LocalOnnxEmbeddingModel, OpenAIEmbeddingModel
from base.config import settings

@pytest.fixture
def mock_settings():
    with patch("base.embedding.embedding_service.settings") as mock_settings:
        mock_settings.embedding_type = "local"
        mock_settings.local_embedding_model_path = "dummy_path"
        mock_settings.local_embedding_tokenizer_path = "dummy_tokenizer_path"
        mock_settings.siliconflow_api_key = "dummy_key"
        mock_settings.siliconflow_embedding_model = "dummy_model"
        mock_settings.siliconflow_base_url = "dummy_url"
        mock_settings.openai_api_key = "dummy_openai_key"
        yield mock_settings

@pytest.fixture
def mock_onnx_deps():
    with patch.dict("sys.modules", {
        "onnxruntime": MagicMock(),
        "tokenizers": MagicMock()
    }):
        yield

@pytest.mark.asyncio
async def test_embedding_service_init_local(mock_settings, mock_onnx_deps):
    with patch("base.embedding.embedding_service.LocalOnnxEmbeddingModel._load_model") as mock_load:
        service = EmbeddingService()
        assert isinstance(service.primary_model, LocalOnnxEmbeddingModel)
        assert service.primary_model.model_path == "dummy_path"

@pytest.mark.asyncio
async def test_embedding_service_fallback(mock_settings, mock_onnx_deps):
    # Mock primary model to fail
    with patch("base.embedding.embedding_service.LocalOnnxEmbeddingModel.embed_text", side_effect=Exception("Local model failed")):
        # Mock fallback model
        with patch("base.embedding.embedding_service.OpenAIEmbeddingModel.embed_text", new_callable=AsyncMock) as mock_fallback_embed:
            mock_fallback_embed.return_value = [0.1, 0.2, 0.3]
            
            # Init service (mock loading)
            with patch("base.embedding.embedding_service.LocalOnnxEmbeddingModel._load_model"):
                service = EmbeddingService()
                
                # Test embed_text
                result = await service.embed_text("test")
                
                assert result == [0.1, 0.2, 0.3]
                mock_fallback_embed.assert_called_once_with("test")

@pytest.mark.asyncio
async def test_embedding_service_all_fail(mock_settings, mock_onnx_deps):
    with patch("base.embedding.embedding_service.LocalOnnxEmbeddingModel.embed_text", side_effect=Exception("Local fail")):
        with patch("base.embedding.embedding_service.OpenAIEmbeddingModel.embed_text", side_effect=Exception("Fallback fail")):
            with patch("base.embedding.embedding_service.LocalOnnxEmbeddingModel._load_model"):
                service = EmbeddingService()
                with pytest.raises(RuntimeError, match="所有嵌入模型均不可用"):
                    await service.embed_text("test")
