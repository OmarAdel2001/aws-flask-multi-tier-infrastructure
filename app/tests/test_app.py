import pytest
import sys
import os

# Add parent directory to sys.path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test the health check endpoint returns 200 and healthy status."""
    rv = client.get('/health')
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert json_data['status'] == 'healthy'
    assert json_data['primary_db'] == 'mock_mode'

def test_index_route(client):
    """Test the main HTML index route renders successfully."""
    rv = client.get('/')
    assert rv.status_code == 200
    assert b"CloudScale Database Tier Console" in rv.data

def test_get_items(client):
    """Test retrieving items in mock mode."""
    rv = client.get('/api/items')
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert json_data['source'] == 'Mock (Local)'
    assert len(json_data['items']) == 2
    assert json_data['items'][0]['name'] == 'Mock Item A'

def test_add_item(client):
    """Test writing a new item in mock mode."""
    payload = {
        "name": "Test Router",
        "description": "Enterprise Core Router",
        "price": 2500.00,
        "quantity": 3
    }
    rv = client.post('/api/items', json=payload)
    assert rv.status_code == 201
    json_data = rv.get_json()
    assert json_data['source'] == 'Mock (Local)'
    assert json_data['item']['name'] == 'Test Router'
    assert json_data['item']['price'] == 2500.00
    assert json_data['item']['quantity'] == 3

def test_add_item_missing_fields(client):
    """Test validation errors when creating items with missing fields."""
    payload = {
        "name": "Invalid Item"
    }
    rv = client.post('/api/items', json=payload)
    assert rv.status_code == 400
    json_data = rv.get_json()
    assert "error" in json_data

def test_get_report(client):
    """Test generating a report on the replica node in mock mode."""
    rv = client.get('/api/report')
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert json_data['source'] == 'Mock (Local)'
    assert len(json_data['report']) == 2
    assert json_data['report'][0]['inventory_value'] == 50.00

def test_db_status(client):
    """Test the DB connection status monitor returns correct configurations in mock mode."""
    rv = client.get('/api/db-status')
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert json_data['primary_configured'] is False
    assert json_data['replica_configured'] is False
    assert json_data['primary_ssl_active'] is False
    assert json_data['replica_ssl_active'] is False
