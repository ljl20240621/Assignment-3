"""
Base Data Access Object - provides common persistence operations.
"""
import pickle
from typing import Dict, List, TypeVar, Generic, Optional
from abc import ABC, abstractmethod

T = TypeVar('T')


class BaseDAO(ABC, Generic[T]):
    """
    Abstract base class for Data Access Objects.
    Provides CRUD operations with pickle-based persistence.
    """
    
    def __init__(self, data_file: str):
        self.data_file = data_file
        self._data: Dict[str, T] = {}
    
    @abstractmethod
    def get_entity_id(self, entity: T) -> str:
        """Get the unique identifier for an entity."""
        pass
    
    def add(self, entity: T) -> None:
        """Add an entity to the data store."""
        entity_id = self.get_entity_id(entity)
        if entity_id in self._data:
            raise ValueError(f"Entity with ID '{entity_id}' already exists.")
        self._data[entity_id] = entity
    
    def update(self, entity: T) -> None:
        """Update an existing entity."""
        entity_id = self.get_entity_id(entity)
        if entity_id not in self._data:
            raise ValueError(f"Entity with ID '{entity_id}' not found.")
        self._data[entity_id] = entity
    
    def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID. Returns True if deleted, False if not found."""
        if entity_id in self._data:
            del self._data[entity_id]
            return True
        return False
    
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get an entity by ID."""
        return self._data.get(entity_id)
    
    def get_all(self) -> List[T]:
        """Get all entities."""
        return list(self._data.values())
    
    def exists(self, entity_id: str) -> bool:
        """Check if an entity exists."""
        return entity_id in self._data
    
    def count(self) -> int:
        """Get the count of entities."""
        return len(self._data)
    
    def clear(self) -> None:
        """Clear all entities."""
        self._data.clear()
    
    def load(self) -> None:
        """Load data from pickle file."""
        try:
            with open(self.data_file, 'rb') as f:
                self._data = pickle.load(f)
        except FileNotFoundError:
            # File doesn't exist yet, start with empty data
            self._data = {}
        except Exception as e:
            raise Exception(f"Failed to load data from {self.data_file}: {e}")
    
    def save(self) -> None:
        """Save data to pickle file."""
        try:
            with open(self.data_file, 'wb') as f:
                pickle.dump(self._data, f)
        except Exception as e:
            raise Exception(f"Failed to save data to {self.data_file}: {e}")

