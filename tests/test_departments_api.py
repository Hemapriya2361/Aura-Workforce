from tests.test_employees_api import seed_five

BASE = "/api/v1/departments"


def test_list_departments(client):
    response = client.get(BASE)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [d["department_id"] for d in body["items"]] == ["D01", "D02"]
    assert body["items"][0]["department_name"] == "Engineering"


def test_list_departments_pagination(client):
    body = client.get(BASE, params={"size": 1, "page": 2}).json()
    assert [d["department_id"] for d in body["items"]] == ["D02"]
    assert body["pages"] == 2


def test_list_departments_invalid_size_returns_422(client):
    assert client.get(BASE, params={"size": 0}).status_code == 422


def test_get_department(client):
    response = client.get(f"{BASE}/D01")
    assert response.status_code == 200
    assert response.json()["cost_center"] == "CC-100"


def test_get_missing_department_returns_404(client):
    response = client.get(f"{BASE}/D99")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_department_employees(client):
    seed_five(client)
    body = client.get(f"{BASE}/D01/employees").json()
    assert body["total"] == 3
    assert {e["department_id"] for e in body["items"]} == {"D01"}


def test_department_employees_are_paginated(client):
    seed_five(client)
    body = client.get(f"{BASE}/D01/employees", params={"size": 2}).json()
    assert len(body["items"]) == 2
    assert body["total"] == 3
    assert body["pages"] == 2


def test_department_without_employees_is_empty(client):
    body = client.get(f"{BASE}/D02/employees").json()
    assert body["items"] == []
    assert body["total"] == 0


def test_employees_of_missing_department_returns_404(client):
    assert client.get(f"{BASE}/D99/employees").status_code == 404