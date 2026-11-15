import pytest

@pytest.mark.example
def test_example_pass():
    assert 1 == 1

@pytest.mark.example
def test_example_fail():
    assert 1 == 2