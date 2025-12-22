import app.services.image_generation as imgsvc


def test_generate_image_endpoint(client, monkeypatch):
    # find seeded patient id
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    uid = patient['id']

    # monkeypatch the external generator to avoid calling ComfyUI
    def fake_generar(prompt_text, user_id, prompt_seed=None, input_img=None):
        return {"message": "ok", "file": "fake.png", "fullPath": "/tmp/fake.png"}

    monkeypatch.setattr(imgsvc, 'generar_imagen', fake_generar)

    payload = {"promptText": "una escena bonita"}
    r = client.post(f'/comfy/users/{uid}/images/', json=payload)
    assert r.status_code == 200
    resp = r.json()
    assert resp['file'] == 'fake.png'


def test_comfy_for_therapist_forbidden(client, monkeypatch):
    # find therapist id
    r = client.get('/users/users/')
    users = r.json()
    therapist = next(u for u in users if u['email'] == 'therapist@example.com')
    tid = therapist['id']

    # monkeypatch comfy generator to avoid external calls
    import app.services.image_generation as imgsvc
    def fake_generar(prompt_text, user_id, prompt_seed=None, input_img=None):
        return {"message": "ok", "file": "fake.png", "fullPath": "/tmp/fake.png"}
    monkeypatch.setattr(imgsvc, 'generar_imagen', fake_generar)

    r = client.post(f'/comfy/users/{tid}/images/', json={"promptText": "x"})
    assert r.status_code == 404
