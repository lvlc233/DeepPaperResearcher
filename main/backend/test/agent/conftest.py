import pytest
import asyncio
from typing import AsyncGenerator

@pytest.fixture
def anyio_backend():
    return 'asyncio'
