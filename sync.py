import hashlib
import time
import aiofiles
import asyncio
from pathlib import Path

CHUNK_SIZE = 8192
SLEEP_INTERVAL = 1


class SyncManager:
    def __init__(self, source, replica, logger, interval):
        """
        SyncManager with async hash calculation and async file copy
        Scans files and directories on source and target recursively

        :param source: Path to source directory
        :param replica: Path to source directory
        :param logger: Logger
        :param interval: Sync interval in seconds
        """
        self.source = Path(source)
        self.target = Path(replica)
        self.logger = logger
        self.interval = interval

    async def calculate_file_hash(self, file_path: Path):
        hash_md5 = hashlib.md5()
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                while True:
                    chunk = await f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (OSError, IOError) as e:
            self.logger.log_error(f"Error reading file {file_path}: {e}")
            return None
        except Exception as e:
            self.logger.log_error(f"Unexpected error while calculating hash for {file_path}: {e}")
            return None

    @staticmethod
    async def iter_files(dir_path: Path):
        for item in dir_path.rglob('*'):
            if item.is_file():
                yield item

    async def copy_file(self, source_file: Path, target_file: Path):
        try:
            async with aiofiles.open(source_file, 'rb') as src_f:
                async with aiofiles.open(target_file, 'wb') as tgt_f:
                    while True:
                        chunk = await src_f.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        await tgt_f.write(chunk)
            self.logger.log_info(f"Copied {source_file} to {target_file}.")
        except Exception as e:
            self.logger.log_error(f"Failed to copy {source_file} to {target_file}: {e}")

    async def sync_files(self, source: Path, replica: Path, interval: int):
        last_sync_time = time.time()

        while True:
            if time.time() - last_sync_time >= int(interval):

                self.logger.log_info(f"Syncing from {source} to {replica}...")

                tasks = []

                async for source_file in self.iter_files(source):
                    relative_path = source_file.relative_to(source)
                    replica_file = replica / relative_path

                    replica_file.parent.mkdir(parents=True, exist_ok=True)

                    try:
                        if not replica_file.exists() or await self.calculate_file_hash(
                                source_file) != await self.calculate_file_hash(replica_file):
                            tasks.append(self.copy_file(source_file, replica_file))
                    except Exception as e:
                        self.logger.log_error(f"Error syncing file {source_file}: {e}")

                for replica_file in replica.rglob('*'):
                    relative_path = replica_file.relative_to(replica)
                    source_file = source / relative_path

                    if not source_file.exists():
                        try:
                            replica_file.unlink()
                            self.logger.log_info(
                                f"Deleted {replica_file} from replica as it was not present in source.")
                        except Exception as e:
                            self.logger.log_error(f"Failed to delete {replica_file}: {e}")

                await asyncio.gather(*tasks)
                last_sync_time = time.time()

                self.logger.log_info(f"Synced {source} to {replica}!")
            await asyncio.sleep(SLEEP_INTERVAL)

    def run_sync(self):
        asyncio.run(self.sync_files(self.source, self.target, self.interval))

