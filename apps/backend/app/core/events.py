from fastapi import FastAPI

from persistence.db.postgres import create_engine_pg, create_session_factory


async def startup_db_clients(app: FastAPI) -> None:
    engine = create_engine_pg()
    app.state.engine_pg = engine

    session_factory = create_session_factory(engine)
    app.state.session_factory = session_factory


async def shutdown_db_clients(app: FastAPI) -> None:
    if app.state.engine_pg:
        await app.state.engine_pg.dispose()
