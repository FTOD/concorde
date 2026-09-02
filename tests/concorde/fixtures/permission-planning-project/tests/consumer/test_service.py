from src.consumer.service import consume


def test_consume() -> None:
    assert consume() == "published"
