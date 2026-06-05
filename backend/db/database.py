from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.config import DATABASE_URL


def make_session_maker() -> async_sessionmaker:
    """
    Create a fresh engine + session maker bound to the *current* event loop.

    In a multi-threaded server each client thread runs its own event loop.
    A module-level engine singleton binds its asyncpg connection pool to the
    loop that first used it, causing "Future attached to a different loop"
    errors on every subsequent thread.  Creating the engine inside each
    dispatch call (with pooling disabled via NullPool) ensures the engine is
    always on the correct loop and is properly disposed after use.
    """
    from sqlalchemy.pool import NullPool
    engine = create_async_engine(DATABASE_URL, echo=True, poolclass=NullPool)
    return async_sessionmaker(engine, expire_on_commit=False)


# Legacy helpers kept for any code that uses get_async_session directly.
# They also use make_session_maker() so they are loop-safe.
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    session_maker = make_session_maker()
    async with session_maker() as session:
        yield session
