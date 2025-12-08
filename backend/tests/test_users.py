import json
from app.schemas import UserCreate, UserType


def test_create_and_login_and_me(client):
    # create a new patient
    payload = {"email": "alice@example.com", "full_name": "Alice Example", "password": "Password1!", "type": "patient"}
    r = client.post('/users/users/', json=payload)
    assert r.status_code == 200
    user = r.json()
    assert user['email'] == payload['email']
    # login via OAuth2 form
    data = {'username': payload['email'], 'password': payload['password']}
    r = client.post('/users/login/', data=data)
    assert r.status_code == 200
    token = r.json().get('access_token')
    assert token
    # get current user
    r = client.get('/users/users/me', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200
    me = r.json()
    assert me['email'] == payload['email']


def test_list_and_get_user(client):
    # list users
    r = client.get('/users/users/')
    assert r.status_code == 200
    arr = r.json()
    assert isinstance(arr, list)
    # get specific user (the seeded patient exists)
    # find seeded patient
    user = next((u for u in arr if u['email'] == 'patient@example.com'), None)
    assert user is not None
    r = client.get(f"/users/users/{user['id']}")
    assert r.status_code == 200
    fetched = r.json()
    assert fetched['email'] == 'patient@example.com'


def test_login_wrong_password(client):
    # seeded patient exists
    r = client.post('/users/login/', data={'username': 'patient@example.com', 'password': 'WrongPass1!'})
    assert r.status_code == 401


def test_create_duplicate_user(client):
    payload = {"email": "patient@example.com", "full_name": "Paciente Prueba", "password": "Password1!", "type": "patient"}
    r = client.post('/users/users/', json=payload)
    assert r.status_code == 400
