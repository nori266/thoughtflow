import pytest
import sys

# add src to path
sys.path.append('src')

# FIXME: how to import from src.bot.py properly?
from bot import get_buttons, default_keyboard, send_random_note

# test functions from src.bot.py
# TODO how to import from src.bot.py?


def test_get_buttons():
    assert get_buttons('in_progress') is not None

def test_send_random_note():
    assert send_random_note is not None
