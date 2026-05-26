from abc import ABC, abstractmethod
from typing import Any, Dict, List
from fornnn.evidence.vfs.base import VFSNode

class ForNnnPlugin(ABC):
    """
    Base class for all fornnn plugins.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the plugin."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Brief description of what the plugin does."""
        pass

    @abstractmethod
    def can_handle(self, node: VFSNode, data: bytes) -> bool:
        """Check if this plugin can parse the given file/node."""
        pass

    @abstractmethod
    def run(self, node: VFSNode, data: bytes) -> Dict[str, Any]:
        """Run the plugin logic and return results."""
        pass

class PluginManager:
    """
    Loads and manages fornnn plugins.
    """
    def __init__(self):
        self.plugins: List[ForNnnPlugin] = []
        self._load_builtins()

    def _load_builtins(self):
        # Placeholder for loading built-in plugins or discovering from folder
        pass

    def get_handlers(self, node: VFSNode, data: bytes) -> List[ForNnnPlugin]:
        return [p for p in self.plugins if p.can_handle(node, data)]
