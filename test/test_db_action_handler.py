import sys

# add src to path
sys.path.append('src')

from db_action_handler import DBActionHandler

# test functions from src.db_action_handlers.py

def test_get_random_note():
    action_handler = DBActionHandler()
    assert action_handler.get_random_note() is not None


def test_show_last_n():
    action_handler = DBActionHandler()
    assert action_handler.show_last_n() is not None


def test_send_plots():
    action_handler = DBActionHandler()
    plot_file = action_handler.send_plots()
    assert isinstance(plot_file, str)
    assert plot_file.endswith('.png')


if __name__ == '__main__':
    test_send_plots()
