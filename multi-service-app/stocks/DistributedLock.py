from pymongo.errors import DuplicateKeyError

class DistributedLock:
    def __init__(self, locks_collection):
        self.locks_collection = locks_collection
        # Ensure a unique index on the resource key
        self.locks_collection.create_index("resource", unique=True)

    def acquire_lock(self, resource: str) -> bool:
        """
        Acquires a lock on the specified resource.
        Returns True if the lock was successfully acquired, False otherwise.
        """
        try:
            self.locks_collection.insert_one({"resource": resource})
            return True
        except DuplicateKeyError:
            return False

    def release_lock(self, resource: str):
        """
        Releases the lock on the specified resource.
        """
        self.locks_collection.delete_one({"resource": resource})
