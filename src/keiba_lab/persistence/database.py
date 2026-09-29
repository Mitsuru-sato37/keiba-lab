from sqlalchemy import Engine, create_engine

from keiba_lab.settings import Settings


def create_database_engine(settings: Settings) -> Engine:
    """Create a connection engine; migrations remain an explicit operator action."""
    return create_engine(settings.database_url.get_secret_value(), future=True)
