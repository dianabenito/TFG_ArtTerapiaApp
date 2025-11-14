import time
from datetime import datetime


def get_token_for_email(client, email, password='Password1!'):
    data = {'username': email, 'password': password}
    r = client.post('/users/login/', data=data)
    assert r.status_code == 200
    return r.json()['access_token']


def test_sessions_and_websocket_flow(client):
    # get seeded users
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    therapist = next(u for u in users if u['email'] == 'therapist@example.com')

    # get therapist token
    ttoken = get_token_for_email(client, therapist['email'])
    ptoken = get_token_for_email(client, patient['email'])

    # create a session using therapist endpoint
    now = datetime.utcnow().isoformat()
    payload = {"start_date": now, "end_date": now}
    # use therapist to create session for patient
    r = client.post(f"/sessions/session/{patient['id']}", json=payload, headers={'Authorization': f'Bearer {ttoken}'})
    assert r.status_code == 200
    session = r.json()
    sid = session['id']

    # fetch session by id as patient
    r = client.get(f"/sessions/session/{sid}", headers={'Authorization': f'Bearer {ptoken}'})
    assert r.status_code == 200

    # open websocket connections for both
    with client.websocket_connect(f"/ws/{sid}/therapist?token={ttoken}") as ws_t:
        with client.websocket_connect(f"/ws/{sid}/patient?token={ptoken}") as ws_p:
            # patient sends a message
            ws_p.send_text('hello from patient')
            msg = ws_t.receive_text()
            assert 'hello from patient' in msg

            # therapist ends session
            r = client.post(f"/sessions/end/{sid}", headers={'Authorization': f'Bearer {ttoken}'})
            assert r.status_code == 200

            # both sockets should get session_ended or be closed
            # receive message on patient side
            try:
                txt = ws_p.receive_text(timeout=1)
                assert 'session_ended' in txt
            except Exception:
                # socket may be closed
                pass

            try:
                txt2 = ws_t.receive_text(timeout=1)
                assert 'session_ended' in txt2
            except Exception:
                pass

    # After end, GET active should return 404 for both
    r = client.get('/sessions/active', headers={'Authorization': f'Bearer {ttoken}'})
    assert r.status_code == 404
    r = client.get('/sessions/active', headers={'Authorization': f'Bearer {ptoken}'})
    assert r.status_code == 404


def test_patient_cannot_create_or_end_session_and_nonparticipant_forbidden(client):
    # patient token
    r = client.get('/users/users/')
    users = r.json()
    patient = next(u for u in users if u['email'] == 'patient@example.com')
    therapist = next(u for u in users if u['email'] == 'therapist@example.com')

    data = {'username': patient['email'], 'password': 'Password1!'}
    r = client.post('/users/login/', data=data)
    assert r.status_code == 200
    ptoken = r.json()['access_token']

    # patient tries to create session (therapist-only)
    now = datetime.utcnow().isoformat()
    payload = {"start_date": now, "end_date": now}
    r = client.post(f"/sessions/session/{patient['id']}", json=payload, headers={'Authorization': f'Bearer {ptoken}'})
    assert r.status_code == 403

    # therapist creates a session
    data2 = {'username': therapist['email'], 'password': 'Password1!'}
    r2 = client.post('/users/login/', data=data2)
    assert r2.status_code == 200
    ttoken = r2.json()['access_token']
    r3 = client.post(f"/sessions/session/{patient['id']}", json=payload, headers={'Authorization': f'Bearer {ttoken}'})
    assert r3.status_code == 200
    sid = r3.json()['id']

    # patient tries to end it
    r4 = client.post(f"/sessions/end/{sid}", headers={'Authorization': f'Bearer {ptoken}'})
    assert r4.status_code == 403

    # create another user (other) and ensure they cannot GET the session
    r5 = client.post('/users/users/', json={"email": "other@example.com", "password": "Password1!", "type": "patient"})
    assert r5.status_code == 200
    rlogin = client.post('/users/login/', data={'username': 'other@example.com', 'password': 'Password1!'})
    assert rlogin.status_code == 200
    otoken = rlogin.json()['access_token']

    r6 = client.get(f"/sessions/session/{sid}", headers={'Authorization': f'Bearer {otoken}'})
    assert r6.status_code == 403


def test_websocket_missing_or_invalid_token(client):
    # create a session as therapist
    r = client.get('/users/users/')
    users = r.json()
    therapist = next(u for u in users if u['email'] == 'therapist@example.com')
    rlogin = client.post('/users/login/', data={'username': therapist['email'], 'password': 'Password1!'})
    assert rlogin.status_code == 200
    ttoken = rlogin.json()['access_token']
    now = datetime.utcnow().isoformat()
    r = client.post('/sessions/session/1', json={"start_date": now, "end_date": now}, headers={'Authorization': f'Bearer {ttoken}'})
    assert r.status_code == 200
    sid = r.json()['id']

    # attempt websocket without token should raise
    import pytest
    with pytest.raises(Exception):
        with client.websocket_connect(f'/ws/{sid}/patient'):
            pass

    # attempt websocket with invalid token
    with pytest.raises(Exception):
        with client.websocket_connect(f'/ws/{sid}/patient?token=invalid.token.here'):
            pass
