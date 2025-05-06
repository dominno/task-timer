import pytest
from abc import ABC

# Attempt to import the StorageProvider
try:
    from src.infra.storage.base import StorageProvider
    from src.domain.session import TaskSession
except ImportError:
    StorageProvider = None  # type: ignore
    TaskSession = None  # type: ignore


# A concrete implementation for testing purposes
class ConcreteStorageProvider(StorageProvider):
    def save_task_session(self, session: TaskSession) -> None:
        pass

    def get_all_sessions(self) -> list[TaskSession]:  # Use list[TaskSession]
        return []

    def clear(self) -> None:
        pass


@pytest.mark.skipif(
    StorageProvider is None,
    reason="StorageProvider not yet implemented or import failed",
)
def test_storage_provider_is_abc():
    """Tests that StorageProvider is an Abstract Base Class."""
    assert issubclass(StorageProvider, ABC), "StorageProvider should inherit from ABC"


@pytest.mark.skipif(
    StorageProvider is None,
    reason="StorageProvider not yet implemented or import failed",
)
def test_storage_provider_cannot_be_instantiated_directly():
    """Tests that StorageProvider cannot be instantiated directly."""
    with pytest.raises(
        TypeError, match="Can't instantiate abstract class StorageProvider"
    ):
        StorageProvider()  # type: ignore


@pytest.mark.skipif(
    StorageProvider is None,
    reason="StorageProvider not yet implemented or import failed",
)
def test_storage_provider_has_abstract_methods():
    """Tests that StorageProvider declares the required abstract methods."""
    expected_abstract_methods = {"save_task_session", "get_all_sessions", "clear"}
    actual_abstract_methods = StorageProvider.__abstractmethods__
    assert actual_abstract_methods == expected_abstract_methods, (
        f"Expected abstract methods {expected_abstract_methods}, "
        f"got {actual_abstract_methods}"
    )


@pytest.mark.skipif(
    StorageProvider is None,
    reason="StorageProvider not yet implemented or import failed",
)
def test_concrete_provider_can_be_instantiated():
    """Tests that a concrete implementation can be instantiated."""
    try:
        provider = ConcreteStorageProvider()
        assert provider is not None
    except Exception as e:
        pytest.fail(f"ConcreteStorageProvider instantiation failed: {e}")


# Test for attempting to instantiate an incomplete provider
@pytest.mark.skipif(
    StorageProvider is None,
    reason="StorageProvider not yet implemented or import failed",
)
def test_incomplete_provider_raises_type_error():
    """Tests that an incomplete concrete provider raises TypeError on instantiation."""

    class IncompleteProvider(StorageProvider):
        def save_task_session(self, session: TaskSession) -> None:  # Use TaskSession
            pass

        # Missing get_all_sessions and clear

    with pytest.raises(
        TypeError, match="Can't instantiate abstract class IncompleteProvider"
    ):
        IncompleteProvider()  # type: ignore
