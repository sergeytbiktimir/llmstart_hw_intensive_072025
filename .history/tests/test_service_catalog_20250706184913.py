import os
import tempfile
import json
import pytest
from src.service_catalog import FileServiceCatalog

@pytest.fixture
def temp_services_file():
    data = [
        {"id": 1, "name": "Test1", "description": "Desc1"},
        {"id": 2, "name": "Test2", "description": "Desc2"}
    ]
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    try:
        yield path
    finally:
        if os.path.exists(path):
            os.remove(path)


def test_get_services(temp_services_file):
    catalog = FileServiceCatalog(path=temp_services_file)
    services = catalog.get_services()
    assert len(services) == 2
    assert services[0]['name'] == 'Test1'
    assert services[1]['description'] == 'Desc2'


def test_empty_services_file():
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('[]')
    try:
        catalog = FileServiceCatalog(path=path)
        services = catalog.get_services()
        assert services == []
    finally:
        if os.path.exists(path):
            os.remove(path) 