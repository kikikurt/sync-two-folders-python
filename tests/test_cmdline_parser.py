import pytest
import argparse
from src.cmdline_parser import CmdlineParser


def test_validate_interval_valid():
    CmdlineParser._CmdlineParser__validate_interval("10")


def test_validate_interval_zero():
    with pytest.raises(argparse.ArgumentTypeError, match="Interval must be a positive integer."):
        CmdlineParser._CmdlineParser__validate_interval("0")


def test_validate_interval_negative():
    with pytest.raises(argparse.ArgumentTypeError, match="Interval must be a positive integer."):
        CmdlineParser._CmdlineParser__validate_interval("-5")


def test_validate_interval_non_integer():
    with pytest.raises(argparse.ArgumentTypeError, match="Interval must be an integer."):
        CmdlineParser._CmdlineParser__validate_interval("ten seconds")


def test_validate_interval_too_large():
    with pytest.raises(argparse.ArgumentTypeError, match="Interval is too large and may cause overflow."):
        CmdlineParser._CmdlineParser__validate_interval(2**63)
