from src.utils.logger import setup_logger

def test_setup_logger():
    logger = setup_logger("test")
    assert logger is not None
