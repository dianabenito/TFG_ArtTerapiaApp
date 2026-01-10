import app.services.image_generation as imgsvc


def test_generate_image_endpoint(client, monkeypatch):
    # monkeypatch the external generator to avoid calling ComfyUI
    def fake_generar(prompt_text, user_id, prompt_seed=None, input_img=None):
        return {"message": "ok", "file": "fake.png", "fullPath": "/tmp/fake.png"}

    monkeypatch.setattr(imgsvc, 'generar_imagen', fake_generar)

    payload = {"promptText": "una escena bonita"}
    headers = {"Authorization": f"Bearer {client.patient_token}"}
    r = client.post(f'/comfy/users/{client.patient_id}/images/', json=payload, headers=headers)
    assert r.status_code == 200
    resp = r.json()
    assert resp['file'] == 'fake.png'


def test_comfy_for_therapist_forbidden(client, monkeypatch):
    # monkeypatch comfy generator to avoid external calls
    import app.services.image_generation as imgsvc
    def fake_generar(prompt_text, user_id, prompt_seed=None, input_img=None):
        return {"message": "ok", "file": "fake.png", "fullPath": "/tmp/fake.png"}
    monkeypatch.setattr(imgsvc, 'generar_imagen', fake_generar)

    headers = {"Authorization": f"Bearer {client.therapist_token}"}
    r = client.post(f'/comfy/users/{client.therapist_id}/images/', json={"promptText": "x"}, headers=headers)
    assert r.status_code == 404
