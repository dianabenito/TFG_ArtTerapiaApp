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


# ===== SKETCH/BOCETO TESTS =====

def test_generate_sketch_image_success(client, monkeypatch):
    """Test successful sketch-to-image conversion"""
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    uid = patient['id']

    recorded = {}

    def fake_convertir_boceto(input_img, input_text):
        recorded['input_img'] = input_img
        recorded['input_text'] = input_text
        return {
            "message": "ok",
            "file": "generated_sketch_123.png",
            "fullPath": "/tmp/generated_sketch_123.png",
            "seed": 7777
        }

    monkeypatch.setattr(imgsvc, 'convertir_boceto_imagen', fake_convertir_boceto)

    payload = {
        "sketchImage": "http://127.0.0.1:8000/images/drawn_images/drawn_abc123.png",
        "sketchText": "convertir este boceto en arte digital"
    }
    r = client.post(f'/comfy/users/{uid}/sketch-images/', json=payload)
    assert r.status_code == 200
    resp = r.json()
    assert resp['file'] == 'generated_sketch_123.png'
    assert resp['seed'] == 7777
    assert recorded['input_img'] == payload['sketchImage']
    assert recorded['input_text'] == payload['sketchText']


def test_generate_sketch_image_missing_text(client):
    """Test sketch endpoint with missing sketchText field"""
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    uid = patient['id']

    # Missing sketchText
    payload = {"sketchImage": "http://127.0.0.1:8000/images/drawn_images/drawn_abc.png"}
    r = client.post(f'/comfy/users/{uid}/sketch-images/', json=payload)
    assert r.status_code == 422


def test_generate_sketch_image_missing_image(client):
    """Test sketch endpoint with missing sketchImage field"""
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    uid = patient['id']

    # Missing sketchImage
    payload = {"sketchText": "convertir boceto"}
    r = client.post(f'/comfy/users/{uid}/sketch-images/', json=payload)
    assert r.status_code == 422


def test_generate_sketch_image_empty_text(client, monkeypatch):
    """Test sketch endpoint with empty sketchText"""
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    uid = patient['id']

    def fake_convertir_boceto(input_img, input_text):
        if not input_text or input_text.strip() == "":
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="El texto no puede estar vacío")
        return {"message": "ok", "file": "sketch.png", "fullPath": "/tmp/sketch.png", "seed": 1111}

    monkeypatch.setattr(imgsvc, 'convertir_boceto_imagen', fake_convertir_boceto)

    payload = {"sketchImage": "http://127.0.0.1:8000/images/drawn_images/drawn_abc.png", "sketchText": ""}
    r = client.post(f'/comfy/users/{uid}/sketch-images/', json=payload)
    assert r.status_code == 400


def test_generate_sketch_image_invalid_image_url(client, monkeypatch):
    """Test sketch endpoint when image file is not found"""
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    uid = patient['id']

    def fake_convertir_boceto(input_img, input_text):
        # Simulate image not found
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Imagen de boceto no encontrada")

    monkeypatch.setattr(imgsvc, 'convertir_boceto_imagen', fake_convertir_boceto)

    payload = {
        "sketchImage": "http://127.0.0.1:8000/images/drawn_images/nonexistent.png",
        "sketchText": "convertir boceto"
    }
    r = client.post(f'/comfy/users/{uid}/sketch-images/', json=payload)
    assert r.status_code == 404


def test_upload_drawn_image_success(client, monkeypatch):
    """Test successful upload of a drawn image from Canvas"""
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    uid = patient['id']

    def fake_publicar_dibujo(upload_file):
        return {
            "message": "ok",
            "file": "drawn_canvas_456.png",
            "fullPath": "/path/to/drawn_canvas_456.png",
            "seed": None
        }

    monkeypatch.setattr(imgsvc, 'publicar_dibujo', fake_publicar_dibujo)

    # Simulate multipart file upload
    from io import BytesIO
    fake_file_content = b"fake image bytes"
    files = {'file': ('drawing.png', BytesIO(fake_file_content), 'image/png')}
    r = client.post(f'/comfy/users/{uid}/images/drawn', files=files)
    assert r.status_code == 200
    resp = r.json()
    assert resp['file'] == 'drawn_canvas_456.png'
    assert resp.get('seed') is None


def test_upload_drawn_image_no_file(client):
    """Test upload drawn endpoint without providing a file"""
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    uid = patient['id']

    # No file provided
    r = client.post(f'/comfy/users/{uid}/images/drawn')
    assert r.status_code == 422


def test_upload_drawn_image_invalid_file_type(client, monkeypatch):
    """Test upload drawn endpoint with invalid file type"""
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    uid = patient['id']

    def fake_publicar_dibujo(upload_file):
        # Validate file type
        if not upload_file.content_type.startswith('image/'):
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")
        return {"message": "ok", "file": "drawn.png", "fullPath": "/tmp/drawn.png", "seed": None}

    monkeypatch.setattr(imgsvc, 'publicar_dibujo', fake_publicar_dibujo)

    from io import BytesIO
    fake_file_content = b"not an image"
    files = {'file': ('drawing.txt', BytesIO(fake_file_content), 'text/plain')}
    r = client.post(f'/comfy/users/{uid}/images/drawn', files=files)
    assert r.status_code == 400


def test_upload_drawn_image_therapist_forbidden(client, monkeypatch):
    """Test that therapists cannot upload drawn images"""
    r = client.get('/users/users/')
    users = r.json()
    therapist = next(u for u in users if u['email'] == 'therapist@example.com')
    tid = therapist['id']

    from io import BytesIO
    fake_file_content = b"fake image bytes"
    files = {'file': ('drawing.png', BytesIO(fake_file_content), 'image/png')}
    r = client.post(f'/comfy/users/{tid}/images/drawn', files=files)
    # Should be rejected because therapists can't have images
    assert r.status_code == 404


def test_sketch_to_image_service_error(client, monkeypatch):
    """Test sketch endpoint when service raises a service error"""
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    uid = patient['id']

    def fake_convertir_boceto(input_img, input_text):
        # Simulate internal service error using HTTPException
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="ComfyUI service unavailable")

    monkeypatch.setattr(imgsvc, 'convertir_boceto_imagen', fake_convertir_boceto)

    payload = {
        "sketchImage": "http://127.0.0.1:8000/images/drawn_images/drawn_abc.png",
        "sketchText": "convertir boceto"
    }
    r = client.post(f'/comfy/users/{uid}/sketch-images/', json=payload)
    # Should return 503 service unavailable
    assert r.status_code == 503


def test_sketch_preserves_seed_in_db(client, monkeypatch):
    """Test that generated sketch images store seed in database"""
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    uid = patient['id']

    def fake_convertir_boceto(input_img, input_text):
        return {
            "message": "ok",
            "file": "generated_from_sketch_999.png",
            "fullPath": "/tmp/generated_from_sketch_999.png",
            "seed": 8888
        }

    monkeypatch.setattr(imgsvc, 'convertir_boceto_imagen', fake_convertir_boceto)

    payload = {
        "sketchImage": "http://127.0.0.1:8000/images/drawn_images/drawn_test.png",
        "sketchText": "arte abstracto"
    }
    r = client.post(f'/comfy/users/{uid}/sketch-images/', json=payload)
    assert r.status_code == 200
    resp = r.json()
    # Verify seed is returned
    assert resp.get('seed') == 8888

    # Verify image was stored in DB by fetching user images
    r_images = client.get(f'/comfy/users/{uid}/images')
    assert r_images.status_code == 200
    images = r_images.json()
    # Should contain at least one image with matching filename
    matching = [img for img in images['data'] if img['fileName'] == 'generated_from_sketch_999.png']
    assert len(matching) > 0
    assert matching[0]['seed'] == 8888
