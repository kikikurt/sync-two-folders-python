import pytest
from unittest.mock import MagicMock
from src.sync import SyncManager
from src.logger import Logger


@pytest.fixture
def temp_dirs(tmp_path):
    source = tmp_path / "source"
    replica = tmp_path / "replica"
    source.mkdir()
    replica.mkdir()
    return source, replica


@pytest.fixture
def mock_logger():
    logger = MagicMock(Logger)
    return logger


@pytest.mark.asyncio
async def test_copy_file(temp_dirs, mock_logger):
    source, replica = temp_dirs
    source_file = source / "test.txt"
    replica_file = replica / "test.txt"

    source_file.write_text("TEST MESSAGE | DATA FILLER")

    sync_manager = SyncManager(source, replica, mock_logger, 10)
    source_file_stat = source_file.stat()
    await sync_manager.copy_file(source_file, replica_file, source_file_stat)

    assert replica_file.exists()
    assert replica_file.read_text() == "TEST MESSAGE | DATA FILLER"
    mock_logger.log_info.assert_called()


@pytest.mark.asyncio
async def test_remove_files(temp_dirs, mock_logger):
    source, replica = temp_dirs
    replica_file = replica / "orphaned.txt"
    replica_file.write_text("DATA FILLER TO DELETABLE FILE")

    sync_manager = SyncManager(source, replica, mock_logger, 10)
    await sync_manager.remove_files(source, replica)

    assert not replica_file.exists()
    mock_logger.log_info.assert_called()