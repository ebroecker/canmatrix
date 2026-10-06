import canmatrix
# tests generated/assisted by AI (mistral-ai) 

def test_toplevel_canmatrix_is_a_class():
    """`canmatrix.CanMatrix` must be the class, not the module."""
    assert isinstance(canmatrix.CanMatrix, type)


def test_toplevel_import_returns_class():
    """`from canmatrix import CanMatrix` yields the class itself."""
    from canmatrix import CanMatrix

    assert isinstance(CanMatrix, type)
    assert CanMatrix is canmatrix.CanMatrix


def test_class_identity_with_private_module():
    """The class is defined in the private module and re-exported."""
    import canmatrix._canmatrix as cm_mod

    # top-level name is the very same class object, not a module
    assert canmatrix.CanMatrix is cm_mod.CanMatrix


def test_pickle_roundtrip():
    """pickle must still resolve the class via its __module__."""
    import pickle

    matrix = canmatrix.CanMatrix()
    restored = pickle.loads(pickle.dumps(matrix))
    assert type(restored) is canmatrix.CanMatrix