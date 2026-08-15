from ingestion.db import engine
from ingestion.models import Base

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print(f"Tables created: {', '.join(Base.metadata.tables)}")
