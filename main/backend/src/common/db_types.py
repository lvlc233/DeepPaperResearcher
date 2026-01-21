from typing import Type, TypeVar, Any, Generic, Optional
from sqlalchemy.types import TypeDecorator, JSON
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class PydanticJSON(TypeDecorator, Generic[T]):
    """
    SQLAlchemy 类型装饰器: 自动将 Pydantic 模型映射到 PostgreSQL JSON/JSONB 列
    
    使用方法:
        class MyTable(SQLModel, table=True):
            data: MyPydanticModel = Field(
                sa_type=PydanticJSON(MyPydanticModel)
            )
    """
    impl = JSON
    cache_ok = True

    def __init__(self, pydantic_model: Type[T], sa_column_type: Any = JSON):
        """
        初始化
        :param pydantic_model: 要映射的 Pydantic 模型类
        :param sa_column_type: 底层数据库列类型，默认为 JSON
        """
        super().__init__()
        self.pydantic_model = pydantic_model
        if isinstance(sa_column_type, type):
            self.impl = sa_column_type()
        else:
            self.impl = sa_column_type

    def process_bind_param(self, value: Optional[T], dialect) -> Any:
        # Python -> DB: 如果是 Pydantic 对象，转为字典/JSON
        if value is None:
            return None
        if isinstance(value, self.pydantic_model):
            return value.model_dump(mode="json")
        if isinstance(value, dict):
            return value
        return value

    def process_result_value(self, value: Any, dialect) -> Optional[T]:
        # DB -> Python: 将 JSON 字典转为 Pydantic 对象
        if value is None:
            return None
        return self.pydantic_model.model_validate(value)
