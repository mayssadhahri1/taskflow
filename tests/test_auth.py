"""Tests de l'inscription, de la connexion et de la protection par jeton."""

from app.security import hash_password, verify_password


def test_hash_et_verification_du_mot_de_passe():
    stored = hash_password("secret-123")
    assert stored != hash_password("secret-123")  # sel différent à chaque fois
    assert verify_password("secret-123", stored)
    assert not verify_password("mauvais", stored)


def test_inscription_puis_connexion(client):
    res = client.post("/api/v1/auth/register", json={"email": "Nour@Example.com", "password": "motdepasse123"})
    assert res.status_code == 201
    assert res.json()["email"] == "nour@example.com"

    res = client.post("/api/v1/auth/login", data={"username": "nour@example.com", "password": "motdepasse123"})
    assert res.status_code == 200
    assert res.json()["token_type"] == "bearer"


def test_email_deja_utilise(client):
    body = {"email": "a@example.com", "password": "motdepasse123"}
    client.post("/api/v1/auth/register", json=body)
    assert client.post("/api/v1/auth/register", json=body).status_code == 409


def test_mot_de_passe_trop_court(client):
    res = client.post("/api/v1/auth/register", json={"email": "a@example.com", "password": "court"})
    assert res.status_code == 422


def test_mauvais_mot_de_passe(client):
    client.post("/api/v1/auth/register", json={"email": "a@example.com", "password": "motdepasse123"})
    res = client.post("/api/v1/auth/login", data={"username": "a@example.com", "password": "faux-faux-faux"})
    assert res.status_code == 401


def test_route_protegee_sans_jeton(client):
    assert client.get("/api/v1/tasks").status_code == 401


def test_jeton_invalide(client):
    res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer nimporte.quoi.ici"})
    assert res.status_code == 401


def test_profil(client, auth):
    assert client.get("/api/v1/auth/me", headers=auth).json()["email"] == "mayssa@example.com"
