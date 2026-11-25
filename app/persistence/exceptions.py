class PersistenceError(Exception):
    pass


class PersistenceNotConfigured(PersistenceError):
    pass


class RecordNotFound(PersistenceError):
    pass


class ImportRejected(PersistenceError):
    def __init__(self,message,diagnostics=()):
        super().__init__(message);self.diagnostics=diagnostics


class UnsafeStoragePath(PersistenceError):
    pass


class DuplicateScheduleVersion(PersistenceError):
    def __init__(self,project_id,version_id):
        super().__init__('This source SHA-256 already exists within the project.')
        self.project_id=project_id;self.version_id=version_id


class CommitOutcomeUnknown(PersistenceError):
    """A file is retained when the database commit outcome cannot be proven."""
    def __init__(self,version_id):
        super().__init__('Database commit outcome is uncertain; source retained for reconciliation.')
        self.version_id=version_id
