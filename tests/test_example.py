"""Before checking this file, please check `conftest.py` first.

The variables in `conftest.py` are available in this file or all test_* files.
"""


def test_example(get_variables):
    """This will get variables from another pytest, `conftest.py`."""
    assert isinstance(get_variables, int)
