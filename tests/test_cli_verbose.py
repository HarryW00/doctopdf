"""Tests for #6: CLI --verbose flag and logging level wiring."""
import logging

from doctopdf.cli import _configure_logging, build_parser


def _reset_root():
    for h in list(logging.root.handlers):
        logging.root.removeHandler(h)
    logging.root.setLevel(logging.WARNING)


def test_parser_verbose_default_false():
    ns = build_parser().parse_args([])
    assert ns.verbose is False


def test_parser_verbose_flag_sets_true():
    ns = build_parser().parse_args(["--verbose"])
    assert ns.verbose is True


def test_configure_logging_verbose_sets_debug():
    _reset_root()
    try:
        _configure_logging(True)
        assert logging.getLogger().level == logging.DEBUG
    finally:
        _reset_root()


def test_configure_logging_default_sets_warning():
    _reset_root()
    try:
        _configure_logging(False)
        assert logging.getLogger().level == logging.WARNING
    finally:
        _reset_root()
