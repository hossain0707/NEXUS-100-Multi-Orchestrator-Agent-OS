import json
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from nexus.config import settings
from nexus.models import Mission


class Base(DeclarativeBase):
    pass


class MissionRecord(Base):
    __tablename__ = "missions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    payload: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


engine = create_async_engine(settings.database_url, pool_pre_ping=True)
Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def save_mission(mission: Mission):
    record = MissionRecord(
        id=str(mission.id),
        status=mission.status.value,
        payload=mission.model_dump_json(),
        updated_at=datetime.now(UTC),
    )
    async with Session() as session:
        await session.merge(record)
        await session.commit()


async def load_mission(mission_id: str) -> Mission | None:
    async with Session() as session:
        record = await session.scalar(
            select(MissionRecord).where(MissionRecord.id == mission_id)
        )
        if not record:
            return None
        return Mission.model_validate(json.loads(record.payload))
