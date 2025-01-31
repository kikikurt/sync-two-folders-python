from logger import Logger


def main():
    logger = Logger("log_test.log")
    for i in range(100000):
        logger.log_info(f"This is log message number {i}")
        if i % 100 == 0:
            logger.log_warning(f"Warning at log number {i}")
        if i % 200 == 0:
            logger.log_error(f"Error at log number {i}")


if __name__ == "__main__":
    main()
