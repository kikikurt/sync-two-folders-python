from logger import Logger
from cmdline_parser import CmdlineParser
from sync import SyncManager


def main():
    args = CmdlineParser.parse_args()

    logger = Logger(args.logfile)

    sync_manager = SyncManager(args.source, args.replica, logger, args.interval)
    sync_manager.run_sync()


if __name__ == "__main__":
    main()
