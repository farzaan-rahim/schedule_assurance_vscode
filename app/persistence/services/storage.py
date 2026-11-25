from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath
from uuid import UUID, uuid4
import os
from app.persistence.exceptions import ImportRejected, UnsafeStoragePath


@dataclass(frozen=True)
class StoredSource:
    id: UUID
    version_id: UUID
    original_filename: str
    storage_filename: str
    relative_path: str
    sha256: str
    byte_size: int
    media_type: str='application/octet-stream'


class LocalSourceStorage:
    def __init__(self,root,maximum_bytes=100*1024*1024):
        self.root=Path(root).resolve();self.maximum_bytes=maximum_bytes

    def validate(self,content,filename):
        if not isinstance(filename,str) or not filename or any(c in filename for c in ('/','\\',':')) or any(ord(c)<32 for c in filename):
            raise UnsafeStoragePath('Source filename must be a plain filename, not a workstation path.')
        if not filename.lower().endswith('.xer'):raise ImportRejected('Only .xer files are accepted.')
        if not content:raise ImportRejected('Empty source files are not accepted.')
        if len(content)>self.maximum_bytes:raise ImportRejected('Source exceeds the configured upload limit.')

    def resolve(self,relative):
        posix=PurePosixPath(relative)
        if posix.is_absolute() or '..' in posix.parts or '\\' in relative or ':' in relative:
            raise UnsafeStoragePath('Storage paths must be relative generated paths.')
        result=(self.root/Path(*posix.parts)).resolve()
        if not result.is_relative_to(self.root):raise UnsafeStoragePath('Storage path escapes the configured root.')
        return result

    def store(self,content,filename,version_id):
        self.validate(content,filename)
        digest=sha256(content).hexdigest()
        source_id=uuid4();storage_name=source_id.hex+'.xer';relative=f'{version_id}/{storage_name}'
        path=self.resolve(relative)
        path.parent.mkdir(parents=True,exist_ok=False)
        try:
            with path.open('xb') as handle:
                handle.write(content);handle.flush();os.fsync(handle.fileno())
        except BaseException:
            if path.exists() and not path.is_symlink():path.unlink()
            try:path.parent.rmdir()
            except OSError:pass
            raise
        return StoredSource(source_id,version_id,filename,storage_name,relative,digest,len(content))

    def remove(self,source):
        path=self.resolve(source.relative_path)
        if path.name!=source.storage_filename or path.parent.name!=str(source.version_id):
            raise UnsafeStoragePath('Cleanup identity does not match the generated source path.')
        if path.is_symlink():raise UnsafeStoragePath('Unexpected storage symlink; cleanup refused.')
        path.unlink(missing_ok=True)
        try:path.parent.rmdir()
        except OSError:pass
