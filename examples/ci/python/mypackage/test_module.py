import pytest

from . import module


def test_myfunc():
    assert module.myfunc(1) == 2
