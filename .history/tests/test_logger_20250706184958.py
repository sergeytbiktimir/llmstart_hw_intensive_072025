import os
import tempfile
import json
import pytest
from src.logger import FileLogger

@pytest.fixture
def temp_log_file():
    fd, path = tempfile.mkstemp(suffix='.log')
    os.close(fd)
    try:
        yield path
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_log_write_and_content(temp_log_file):
    logger = FileLogger(file_path=temp_log_file)
    logger.log('INFO', 'test message', user_id=42, event_type='test')
    with open(temp_log_file, encoding='utf-8') as f:
        lines = f.readlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record['level'] == 'INFO'
    assert record['message'] == 'test message'
    assert record['user_id'] == 42
    assert record['event_type'] == 'test'

def test_log_rotation(temp_log_file):
    logger = FileLogger(file_path=temp_log_file)
    logger.MAX_SIZE = 1024  # 1 KB for test
    # Заполняем лог до ротации
    for i in range(110):
        logger.log('INFO', f'msg{i}', user_id=i)
    # Проверяем, что файл был ротирован
    rotated_files = [f for f in os.listdir(os.path.dirname(temp_log_file)) if os.path.basename(temp_log_file) in f and f != os.path.basename(temp_log_file)]
    assert any('.log.' in f for f in rotated_files)

def test_log_should_not_write_below_level(temp_log_file, monkeypatch):
    logger = FileLogger(file_path=temp_log_file)
    monkeypatch.setenv('LOG_LEVEL', 'ERROR')
    logger.log('INFO', 'should not log')
    with open(temp_log_file, encoding='utf-8') as f:
        content = f.read()
    assert content == '' 