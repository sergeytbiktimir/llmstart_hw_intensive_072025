import os
import tempfile
import pytest
from src.storage import SQLiteStorage

@pytest.fixture
def temp_db_path():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    try:
        yield path
    finally:
        if os.path.exists(path):
            os.remove(path)

@pytest.fixture
def storage(temp_db_path):
    s = SQLiteStorage(db_path=temp_db_path)
    yield s

def test_save_and_get_contact(storage):
    storage.save_contact(1, 'Alice', '+123')
    contacts = storage.get_contacts()
    assert any(c['user_id'] == 1 and c['name'] == 'Alice' and c['contact'] == '+123' for c in contacts)

def test_save_and_get_history(storage):
    storage.save_history(1, 'test_action', 'details')
    history = storage.get_history(1)
    assert any(h['user_id'] == 1 and h['action'] == 'test_action' and h['details'] == 'details' for h in history)

def test_empty_contacts_and_history(storage):
    assert storage.get_contacts() == []
    assert storage.get_history(42) == [] 