import app.services.image_generation as imgsvc


def test_generate_with_seed(client, monkeypatch):
    # find seeded patient id
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    uid = patient['id']

    called = {}

    def fake_generar(prompt_text, prompt_seed=None, input_img=None):
        # record the seed received and return a fake file
        called['seed'] = prompt_seed
        return {"message": "ok", "file": "fake_seed.png", "fullPath": "/tmp/fake_seed.png", "seed": prompt_seed}

    monkeypatch.setattr(imgsvc, 'generar_imagen', fake_generar)

    payload = {"promptText": "prueba con seed", "seed": 12345}
    r = client.post(f'/comfy/users/{uid}/images/', json=payload)
    assert r.status_code == 200
    resp = r.json()
    assert resp['file'] == 'fake_seed.png'
    assert called.get('seed') == 12345


def test_generate_from_existing_image(client, monkeypatch):
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    uid = patient['id']

    recorded = {}

    def fake_generar(prompt_text, prompt_seed=None, input_img=None):
        # ensure input_img value is forwarded
        recorded['input_img'] = input_img
        return {"message": "ok", "file": "from_img.png", "fullPath": "/tmp/from_img.png", "seed": prompt_seed}

    monkeypatch.setattr(imgsvc, 'generar_imagen', fake_generar)

    img_url = "/images/uploaded_images/test_upload.png"
    payload = {"promptText": "usar imagen existente", "inputImage": img_url}
    r = client.post(f'/comfy/users/{uid}/images/', json=payload)
    assert r.status_code == 200
    resp = r.json()
    assert resp['file'] == 'from_img.png'
    assert recorded.get('input_img') == img_url


def test_regenerate_maintaining_seed_flow(client, monkeypatch):
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    uid = patient['id']

    calls = []

    def fake_generar(prompt_text, prompt_seed=None, input_img=None):
        # first call: no seed provided -> produce seed 999
        if prompt_seed is None:
            calls.append(('first', None))
            return {"message": "ok", "file": "first.png", "fullPath": "/tmp/first.png", "seed": 999}
        # subsequent calls should receive the seed and return another file
        calls.append(('later', prompt_seed))
        return {"message": "ok", "file": "later.png", "fullPath": "/tmp/later.png", "seed": prompt_seed}

    monkeypatch.setattr(imgsvc, 'generar_imagen', fake_generar)

    # initial generation (no seed)
    payload1 = {"promptText": "generar sin seed"}
    r1 = client.post(f'/comfy/users/{uid}/images/', json=payload1)
    assert r1.status_code == 200
    resp1 = r1.json()
    assert resp1['file'] == 'first.png'
    seed_generated = resp1.get('seed')
    assert seed_generated == 999

    # regenerate using the returned seed
    payload2 = {"promptText": "regenerar", "seed": seed_generated}
    r2 = client.post(f'/comfy/users/{uid}/images/', json=payload2)
    assert r2.status_code == 200
    resp2 = r2.json()
    assert resp2['file'] == 'later.png'
    # ensure the fake received the seed on the second call
    assert calls[1][1] == 999


def test_generate_by_multiple_images_endpoint(client, monkeypatch):
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    uid = patient['id']

    recorded = {}

    def fake_mult(images_list, count=0):
        # ensure images_list is a list of dicts or filenames
        recorded['images'] = images_list
        recorded['count'] = count
        return {"message": "ok", "file": "mix.png", "fullPath": "/tmp/mix.png", "seed": 4242}

    monkeypatch.setattr(imgsvc, 'generate_image_by_mult_images', fake_mult)

    payload = {"data": [{"fileName": "template1.png"}, {"fileName": "template2.png"}], "count": 2}
    r = client.post(f'/comfy/users/{uid}/multiple-images/', json=payload)
    assert r.status_code == 200
    resp = r.json()
    assert resp['file'] == 'mix.png'
    # backend should have forwarded the list (we expect the service fake to receive the list)
    assert isinstance(recorded.get('images'), list)
    assert recorded['count'] == 2


def test_generate_with_invalid_seed_type(client, monkeypatch):
    # seed must be an int; sending a string should return 422
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    uid = patient['id']

    payload = {"promptText": "prueba", "seed": "not-an-int"}
    r = client.post(f'/comfy/users/{uid}/images/', json=payload)
    assert r.status_code == 422


def test_generate_from_existing_image_not_found(monkeypatch, client):
    # simulate service raising HTTPException when input image missing
    from fastapi import HTTPException
    def fake_generar(prompt_text, prompt_seed=None, input_img=None):
        raise HTTPException(status_code=400, detail="Imagen no encontrada")

    monkeypatch.setattr(imgsvc, 'generar_imagen', fake_generar)

    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    uid = patient['id']

    payload = {"promptText": "usar imagen", "inputImage": "/images/uploaded_images/doesnotexist.png"}
    r = client.post(f'/comfy/users/{uid}/images/', json=payload)
    assert r.status_code == 400


def test_multiple_images_too_few_and_too_many(client, monkeypatch):
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    uid = patient['id']

    # too few (1)
    def fake_mult_validate(images_list, count=0):
        if len(images_list) < 2 or len(images_list) > 4:
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail="Invalid number of images")
        return {"message": "ok", "file": "mix.png", "fullPath": "/tmp/mix.png", "seed": 4242}

    monkeypatch.setattr(imgsvc, 'generate_image_by_mult_images', fake_mult_validate)

    payload_too_few = {"data": [{"fileName": "template1.png"}], "count": 1}
    r1 = client.post(f'/comfy/users/{uid}/multiple-images/', json=payload_too_few)
    assert r1.status_code == 422

    # too many (5)
    payload_too_many = {"data": [{"fileName": "t1.png"}, {"fileName": "t2.png"}, {"fileName": "t3.png"}, {"fileName": "t4.png"}, {"fileName": "t5.png"}], "count": 5}
    r2 = client.post(f'/comfy/users/{uid}/multiple-images/', json=payload_too_many)
    assert r2.status_code == 422


def test_multiple_images_malformed_payload(client):
    # missing 'data' should lead to 422 from Pydantic validation
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    uid = patient['id']

    malformed = {"count": 2}
    r = client.post(f'/comfy/users/{uid}/multiple-images/', json=malformed)
    assert r.status_code == 422
