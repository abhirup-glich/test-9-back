try:
    from .main import create_app
except ImportError:
    from main import create_app

app = create_app()

__all__ = ["app", "create_app"]

