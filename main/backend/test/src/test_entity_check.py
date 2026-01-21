
from sqlmodel import SQLModel, create_engine
from base.pg.entity import Layer, Annotation

def test_entity_relationships():
    # This should trigger mapper configuration
    engine = create_engine("sqlite:///")
    SQLModel.metadata.create_all(engine)
    print("Entities created successfully")

if __name__ == "__main__":
    test_entity_relationships()
