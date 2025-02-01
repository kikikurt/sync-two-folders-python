from logger import Logger
from cmdline_parser import CmdlineParser


def main():
    args = CmdlineParser.parse_args()
    print((args.source, args.replica, args.interval, args.logfile))

    logger = Logger(args.logfile)


if __name__ == "__main__":
    main()
