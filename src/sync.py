import aiofiles
import asyncio
from pathlib import Path
import os
import time
import shutil

CHUNK_SIZE = 8192
TASKS_PER_CORE = 2


class SyncManager:
    def __init__(self, source: str, replica: str, logger, interval: int):
        """
        SyncManager
        Syncs files and directories from source to replica folders

        :param source: Path to source directory
        :param replica: Path to replica directory
        :param logger: Logger
        :param interval: Sync interval in seconds
        """
        self.source = Path(source)
        self.replica = Path(replica)
        self.logger = logger
        self.interval = interval

        concurrent_tasks_optimum = os.cpu_count() * TASKS_PER_CORE
        self.max_concurrent_tasks = concurrent_tasks_optimum
        self.semaphore = asyncio.Semaphore(concurrent_tasks_optimum)

    def calculate_time_to_wait(self, start_time: time, interval: int):
        elapsed_time = time.time() - start_time
        time_difference = interval - elapsed_time
        return max(0, time_difference)

    async def file_exists(self, path: Path):
        try:
            await asyncio.to_thread(os.stat, path)
            return True
        except FileNotFoundError:
            return False

    async def iter_files(self, folder_path: Path):
        files = await asyncio.to_thread(list, folder_path.rglob('*'))
        file_items = [item for item in files if await asyncio.to_thread(item.is_file)]
        for item in file_items:
            yield item

    def iter_folders(self, path: Path):
        path = Path(path)
        if path.exists():
            for subdir in path.iterdir():
                if subdir.is_dir():
                    yield subdir
                    yield from self.iter_folders(subdir)

    def copy_folders(self, source: Path, replica: Path):
        for folder_in_source in self.iter_folders(source):
            relative_path = folder_in_source.relative_to(source)
            replica_folder = replica / relative_path

            if not replica_folder.exists():
                try:
                    replica_folder.mkdir(parents=True, exist_ok=True)
                    self.logger.log_info(f"Created folder {replica_folder} in replica to match source.")
                except Exception as e:
                    self.logger.log_error(f"Failed to create {replica_folder}: {e}")

    async def copy_file(self, source_file: Path, replica_file: Path, source_file_stat: os.stat_result):
        async with self.semaphore:
            try:
                async with aiofiles.open(source_file, 'rb') as src_f:
                    async with aiofiles.open(replica_file, 'wb') as rpl_f:
                        while True:
                            chunk = await src_f.read(CHUNK_SIZE)
                            if not chunk:
                                break
                            await rpl_f.write(chunk)
                os.utime(replica_file, (source_file_stat.st_atime, source_file_stat.st_mtime))
                self.logger.log_info(f"Copied {source_file} to {replica_file}.")
            except Exception as e:
                self.logger.log_error(f"Failed to copy {source_file} to {replica_file}: {e}")

    async def copy_files(self, source: Path, replica: Path):
        tasks = []
        async for source_file in self.iter_files(source):
            relative_path = source_file.relative_to(source)
            replica_file = replica / relative_path

            try:
                source_file_stat = source_file.stat()
                if not await self.file_exists(replica_file):
                    tasks.append(self.copy_file(source_file, replica_file, source_file_stat))
                else:
                    if source_file_stat.st_mtime != replica_file.stat().st_mtime or \
                            source_file_stat.st_size != replica_file.stat().st_size:
                        tasks.append(self.copy_file(source_file, replica_file, source_file_stat))
            except Exception as e:
                self.logger.log_error(f"Error syncing file {source_file}: {e}")

        await asyncio.gather(*tasks)

    async def remove_files(self, source: Path, replica: Path):
        async for replica_file in self.iter_files(replica):
            relative_path = replica_file.relative_to(replica)
            source_file = source / relative_path

            if not source_file.exists():
                try:
                    replica_file.unlink()
                    self.logger.log_info(f"Deleted {replica_file} from replica as it was not present in source.")
                except Exception as e:
                    self.logger.log_error(f"Failed to delete {replica_file}: {e}")

    def remove_folders(self, source: Path, replica: Path):
        for folder_in_replica in self.iter_folders(replica):
            relative_path = folder_in_replica.relative_to(replica)
            source_folder = source / relative_path

            if not source_folder.exists():
                try:
                    shutil.rmtree(folder_in_replica, ignore_errors=True)
                    self.logger.log_info(f"Deleted folder(s) with root {folder_in_replica} from replica as it was "
                                         f"not present in source.")
                except Exception as e:
                    self.logger.log_error(f"Failed to delete {folder_in_replica}: {e}")

    async def sync_files(self, source: Path, replica: Path, interval: int):
        try:
            while True:
                start_time = time.time()
                self.logger.log_info(f"Syncing from {source} to {replica}...")

                await self.remove_files(source, replica)
                self.copy_folders(source, replica)
                await self.copy_files(source, replica)
                self.remove_folders(source, replica)

                time_to_wait = self.calculate_time_to_wait(start_time, interval)

                self.logger.log_info(f"Synced {source} to {replica}!")
                self.logger.log_info(
                    f"Next sync cycle starts in {time_to_wait:.2f} seconds"
                    if time_to_wait > 0
                    else f"Sync took more than {interval} seconds. Executing new sync immediately"
                )

                await asyncio.sleep(time_to_wait)
        except asyncio.CancelledError:
            self.logger.log_info("Sync process interrupted by user.")

    def run_sync(self):
        asyncio.run(self.sync_files(self.source, self.replica, int(self.interval)))
