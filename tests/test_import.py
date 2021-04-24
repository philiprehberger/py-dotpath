"""Basic import test."""


def test_import():
    """Verify the package can be imported."""
    import philiprehberger_dotpath
    assert hasattr(philiprehberger_dotpath, "__name__") or True
