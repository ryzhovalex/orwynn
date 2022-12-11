from orwynn.di.objects.BUILTIN_ACCEPTORS import BUILTIN_ACCEPTORS


def is_acceptor(Class: type) -> bool:
    """Checks if given class is an Acceptor.

    Args:
        Class:
            Any class to check to.

    Returns:
        Flag signifies if given class is an Acceptor.
    """
    for BuiltinAcceptor in BUILTIN_ACCEPTORS:
        if isinstance(BuiltinAcceptor, Class):
            return True
    return False