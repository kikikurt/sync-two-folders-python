import argparse
import os
import sys


class CmdlineParser:
    """
    Parses and validates cmdline args
    """
    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser(description="Parse args")
        parser.add_argument('-s', '--source', dest='source', help="Path to the source folder")
        parser.add_argument('-r', '--replica', dest='replica', help="Path to the replica folder")
        parser.add_argument('-i', '--interval', dest='interval', help="Synchronization interval in seconds")
        parser.add_argument('-l', '--logfile', dest='logfile', help="Path to the log file")

        args = parser.parse_args()
        CmdlineParser.__validate_args(args)
        return args

    @staticmethod
    def __validate_args(args: argparse.Namespace):
        CmdlineParser.__validate_interval(args.interval)
        CmdlineParser.__validate_path_existence(args.source, "source")
        CmdlineParser.__validate_path_existence(args.replica, "replica")
        CmdlineParser.__validate_permissions(args.source, "source")
        CmdlineParser.__validate_permissions(args.replica, "replica")
        CmdlineParser.__validate_logfile_lock(args.logfile)

    @staticmethod
    def __validate_interval(interval: int):
        try:
            interval = int(interval)
        except ValueError:
            raise argparse.ArgumentTypeError("Interval must be an integer.")

        if interval <= 0:
            raise argparse.ArgumentTypeError("Interval must be a positive integer.")
        if interval > sys.maxsize:
            raise argparse.ArgumentTypeError("Interval is too large and may cause overflow.")

    @staticmethod
    def __validate_path_existence(path: str, name: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"{name} path '{path}' does not exist.")

    @staticmethod
    def __validate_permissions(path: str, name: str):
        if not os.access(path, os.R_OK):
            raise PermissionError(f"No read access to {name} path: {path}")
        if not os.access(path, os.W_OK):
            raise PermissionError(f"No write access to {name} path: {path}")

    @staticmethod
    def __validate_logfile_lock(logfile: str):
        try:
            with open(logfile, 'a') as log:
                pass
        except IOError:
            print(f"Warning: Log file '{logfile}' is not writable or is locked.")
