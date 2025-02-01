import aiofiles
import asyncio
from pathlib import Path
import os

CHUNK_SIZE = 8192


class SyncManager:
    def __init__(self, source, replica, logger, interval):
        """
        SyncManager
        Syncs files and directories on source and replica recursively

        :param source: Path to source directory
        :param replica: Path to replica directory
        :param logger: Logger
        :param interval: Sync interval in seconds
        """
        self.source = Path(source)
        self.target = Path(replica)
        self.logger = logger
        self.interval = interval

        concurrent_tasks_optimum = os.cpu_count() * 2
        self.max_concurrent_tasks = concurrent_tasks_optimum
        self.semaphore = asyncio.Semaphore(concurrent_tasks_optimum)

    async def file_exists(self, path: Path):
        try:
            await asyncio.to_thread(os.stat, path)
            return True
        except FileNotFoundError:
            return False

    async def iter_files(self, dir_path: Path):
        files = await asyncio.to_thread(list, dir_path.rglob('*'))
        for item in files:
            is_file = await asyncio.to_thread(item.is_file)
            if is_file:
                yield item

    async def copy_file(self, source_file: Path, target_file: Path):
        async with self.semaphore:
            try:
                async with aiofiles.open(source_file, 'rb') as src_f:
                    async with aiofiles.open(target_file, 'wb') as tgt_f:
                        while True:
                            chunk = await src_f.read(CHUNK_SIZE)
                            if not chunk:
                                break
                            await tgt_f.write(chunk)
                os.utime(target_file, (source_file.stat().st_atime, source_file.stat().st_mtime))
                self.logger.log_info(f"Copied {source_file} to {target_file}.")
            except Exception as e:
                self.logger.log_error(f"Failed to copy {source_file} to {target_file}: {e}")

    async def copy_files(self, source: Path, replica: Path):
        tasks = []
        async for source_file in self.iter_files(source):
            relative_path = source_file.relative_to(source)
            replica_file = replica / relative_path

            replica_file.parent.mkdir(parents=True, exist_ok=True)

            try:
                if not await self.file_exists(replica_file):
                    tasks.append(self.copy_file(source_file, replica_file))
                else:
                    if source_file.stat().st_mtime != replica_file.stat().st_mtime or \
                            source_file.stat().st_size != replica_file.stat().st_size:
                            tasks.append(self.copy_file(source_file, replica_file))
            except Exception as e:
                self.logger.log_error(f"Error syncing file {source_file}: {e}")

        await asyncio.gather(*tasks)

    async def remove_files(self, source: Path, replica: Path):
        for replica_file in replica.rglob('*'):
            relative_path = replica_file.relative_to(replica)
            source_file = source / relative_path

            if not source_file.exists():
                try:
                    replica_file.unlink()
                    self.logger.log_info(f"Deleted {replica_file} from replica as it was not present in source.")
                except Exception as e:
                    self.logger.log_error(f"Failed to delete {replica_file}: {e}")

    async def sync_files(self, source: Path, replica: Path, interval: int):
        try:
            while True:
                self.logger.log_info(f"Syncing from {source} to {replica}...")

                await self.copy_files(source, replica)
                await self.remove_files(source, replica)

                self.logger.log_info(f"Synced {source} to {replica}!")

                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            self.logger.log_info("Sync process interrupted by user.")

    def run_sync(self):
        asyncio.run(self.sync_files(self.source, self.target, int(self.interval)))

