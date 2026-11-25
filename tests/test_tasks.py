"""Tests du CRUD des tâches, des filtres, des statistiques et de l'isolation entre utilisateurs."""

from datetime import date, timedelta

from tests.conftest import register_and_login

URL = "/api/v1/tasks"


def test_creer_et_lire_une_tache(client, auth):
    res = client.post(URL, json={"title": "Préparer le rapport PFE", "priority": "high"}, headers=auth)
    assert res.status_code == 201
    task = res.json()
    assert task["status"] == "todo"
    assert client.get(f"{URL}/{task['id']}", headers=auth).json()["title"] == "Préparer le rapport PFE"


def test_titre_obligatoire(client, auth):
    assert client.post(URL, json={"title": ""}, headers=auth).status_code == 422


def test_mise_a_jour_partielle(client, auth):
    task_id = client.post(URL, json={"title": "Écrire les tests"}, headers=auth).json()["id"]
    res = client.patch(f"{URL}/{task_id}", json={"status": "done"}, headers=auth)
    assert res.status_code == 200
    assert res.json()["status"] == "done"
    assert res.json()["title"] == "Écrire les tests"  # inchangé


def test_suppression(client, auth):
    task_id = client.post(URL, json={"title": "À supprimer"}, headers=auth).json()["id"]
    assert client.delete(f"{URL}/{task_id}", headers=auth).status_code == 204
    assert client.get(f"{URL}/{task_id}", headers=auth).status_code == 404


def test_filtres_recherche_et_pagination(client, auth):
    for i in range(5):
        client.post(URL, json={"title": f"Tâche {i}", "priority": "high" if i % 2 else "low"}, headers=auth)
    client.post(URL, json={"title": "Configurer Jenkins"}, headers=auth)

    page = client.get(f"{URL}?limit=2&offset=0", headers=auth).json()
    assert page["total"] == 6 and len(page["items"]) == 2

    assert client.get(f"{URL}?priority=high", headers=auth).json()["total"] == 2
    assert client.get(f"{URL}?q=jenkins", headers=auth).json()["total"] == 1


def test_statistiques(client, auth):
    hier = (date.today() - timedelta(days=1)).isoformat()
    client.post(URL, json={"title": "En retard", "due_date": hier}, headers=auth)
    done_id = client.post(URL, json={"title": "Finie"}, headers=auth).json()["id"]
    client.patch(f"{URL}/{done_id}", json={"status": "done"}, headers=auth)

    stats = client.get(f"{URL}/stats", headers=auth).json()
    assert stats == {"total": 2, "todo": 1, "doing": 0, "done": 1, "overdue": 1, "completion_rate": 0.5}


def test_un_utilisateur_ne_voit_pas_les_taches_des_autres(client, auth):
    task_id = client.post(URL, json={"title": "Privée"}, headers=auth).json()["id"]
    autre = register_and_login(client, email="autre@example.com")

    assert client.get(f"{URL}/{task_id}", headers=autre).status_code == 404
    assert client.patch(f"{URL}/{task_id}", json={"title": "Piratée"}, headers=autre).status_code == 404
    assert client.delete(f"{URL}/{task_id}", headers=autre).status_code == 404
    assert client.get(URL, headers=autre).json()["total"] == 0


def test_sondes_et_metriques(client):
    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/health/ready").status_code == 200
    metrics = client.get("/metrics").text
    assert "http_requests_total" in metrics
