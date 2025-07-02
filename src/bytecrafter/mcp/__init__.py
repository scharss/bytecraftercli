from importlib import metadata

__all__ = [
    "transport_stdio",
    "server_registry",
]

try:
    __version__ = metadata.version("bytecrafter")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0" 