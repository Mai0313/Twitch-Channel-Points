"""This file is an example of how you can pre-define some variables to be used in your tests."""

import pytest


@pytest.fixture(scope="session", autouse=True)
def get_variables():
    """This is a sample of how you can send variables to another pytest."""
    return 500
