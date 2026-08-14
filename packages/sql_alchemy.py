import os
from typing import Generator
from typing import List
from typing import Optional
from sqlalchemy import String
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import Session
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import sessionmaker


class Base(DeclarativeBase):
    pass


class ChatHistory(Base):
    __tablename__ = "chat_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    checkpoint_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    latest_message: Mapped[str] = mapped_column(String(200))

    def __repr__(self) -> str:
        return f"ChatHistory(id={self.id!r}, checkpoint_id={self.checkpoint_id!r}, latest_message={self.latest_message!r})"


DATABASE_PATH = os.environ.get("DATABASE_PATH", "app.db")
engine = create_engine(f"sqlite:///{DATABASE_PATH}", connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_chat_history(session: Session, checkpoint_id: str, latest_message: str) -> ChatHistory:
    chat_history = ChatHistory(checkpoint_id=checkpoint_id, latest_message=latest_message)
    session.add(chat_history)
    session.commit()
    return chat_history


def get_chat_history(session: Session, checkpoint_id: str) -> Optional[ChatHistory]:
    return session.query(ChatHistory).filter_by(checkpoint_id=checkpoint_id).first()


def list_chat_histories(session: Session) -> List[ChatHistory]:
    return session.query(ChatHistory).all()


def update_latest_message(session: Session, checkpoint_id: str, latest_message: str) -> Optional[ChatHistory]:
    chat_history = get_chat_history(session, checkpoint_id)
    if chat_history is None:
        return None
    chat_history.latest_message = latest_message
    session.commit()
    return chat_history
