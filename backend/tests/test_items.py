def test_create_update_delete_item(client):
    # find seeded patient id
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    uid = patient['id']

    # create item
    payload = {"title": "Test item", "description": "desc"}
    r = client.post(f"/items/users/{uid}/items/", json=payload)
    assert r.status_code == 200
    item = r.json()
    assert item['title'] == payload['title']

    # list items
    r = client.get('/items/items/')
    assert r.status_code == 200
    items = r.json()
    assert any(it['id'] == item['id'] for it in items)

    # update item
    updated = {"id": item['id'], "owner_id": item['owner_id'], "title": "Updated", "description": "new"}
    r = client.put(f"/items/items/{item['id']}", json=updated)
    assert r.status_code == 200
    it2 = r.json()
    assert it2['title'] == 'Updated'

    # delete
    r = client.delete(f"/items/items/{item['id']}")
    assert r.status_code == 200
    r = client.get('/items/items/')
    items2 = r.json()
    assert not any(it['id'] == item['id'] for it in items2)


def test_create_item_for_nonexistent_user(client):
    r = client.post('/items/users/9999/items/', json={"title": "X", "description": "Y"})
    assert r.status_code == 404


def test_update_nonexistent_item(client):
    payload = {"id": 9999, "owner_id": 1, "title": "X", "description": "Y"}
    r = client.put('/items/items/9999', json=payload)
    assert r.status_code == 404


def test_delete_nonexistent_item(client):
    r = client.delete('/items/items/9999')
    assert r.status_code == 404
