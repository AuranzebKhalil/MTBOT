from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

class IExecutionLockStore(ABC):
    @abstractmethod
    def acquire(self, key: str, owner_id: str, ttl_seconds: int) -> bool: pass
    @abstractmethod
    def release(self, key: str, owner_id: str) -> bool: pass
    @abstractmethod
    def exists(self, key: str) -> bool: pass
    @abstractmethod
    def cleanup_expired(self) -> int: pass

class SQLiteExecutionLockStore(IExecutionLockStore):
    """
    Assumes a table: execution_locks (key PRIMARY KEY, owner_id, expires_at)
    Atomic inserts guarantee only 1 worker can acquire the lock.
    """
    def __init__(self, db_session):
        self.db = db_session

    def acquire(self, key: str, owner_id: str, ttl_seconds: int = 15) -> bool:
        self.cleanup_expired()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        try:
            # Atomic DB insert ignores constraints if key already exists
            query = """INSERT INTO execution_locks (key, owner_id, expires_at)
                       VALUES (:key, :owner, :exp)"""
            self.db.execute(query, {"key": key, "owner": owner_id, "exp": expires_at})
            self.db.commit()
            return True
        except Exception: # IntegrityError
            self.db.rollback()
            return False

    def exists(self, key: str) -> bool:
        query = "SELECT 1 FROM execution_locks WHERE key = :key AND expires_at > :now"
        res = self.db.execute(query, {"key": key, "now": datetime.now(timezone.utc)}).first()
        return res is not None

    def release(self, key: str, owner_id: str) -> bool:
        query = "DELETE FROM execution_locks WHERE key = :key AND owner_id = :owner"
        self.db.execute(query, {"key": key, "owner": owner_id})
        self.db.commit()
        return True

    def cleanup_expired(self) -> int:
        query = "DELETE FROM execution_locks WHERE expires_at <= :now"
        res = self.db.execute(query, {"now": datetime.now(timezone.utc)})
        self.db.commit()
        return res.rowcount
