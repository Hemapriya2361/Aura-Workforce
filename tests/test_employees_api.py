BASE = "/api/v1/employees"


def payload(**overrides):
    data = {
        "first_name": "Asha",
        "last_name": "Kumar",
        "work_email": "asha.kumar@znova-demo.example",
        "gender": "Female",
        "date_of_birth": "1992-04-10",
        "hire_date": "2024-06-03",
        "department_id": "D01",
        "role_id": "R002",
        "work_location": "Chennai",
        "work_mode": "Hybrid",
        "highest_education": "MCA",
        "commute_distance_km": 12.5,
    }
    data.update(overrides)
    return data


def create(client, first, last="Nair", **overrides):
    email = f"{first.lower()}.{last.lower()}@znova-demo.example"
    body = payload(first_name=first, last_name=last, work_email=email, **overrides)
    response = client.post(BASE, json=body)
    assert response.status_code == 201, response.text
    return response.json()


def error_fields(response):
    return [d["field"] for d in response.json()["error"]["details"]]


def seed_five(client):
    a = create(client, "Asha", hire_date="2024-06-03")
    create(client, "Bala", department_id="D01", work_mode="Remote",
           work_location="Pune", hire_date="2021-01-10", manager_id=a["employee_id"])
    create(client, "Charu", department_id="D02", role_id="R010", work_mode="Onsite",
           hire_date="2019-03-01")
    create(client, "Divya", department_id="D02", role_id="R010",
           work_location="Pune", hire_date="2023-09-15", manager_id=a["employee_id"])
    create(client, "Esha", hire_date="2025-02-20")
    return a


# ---------- create ----------

def test_create_employee(client):
    response = client.post(BASE, json=payload(work_email="Asha.Kumar@Znova-Demo.example"))
    assert response.status_code == 201
    body = response.json()
    assert body["employee_id"] == "EMP-0001"
    assert body["full_name"] == "Asha Kumar"
    assert body["work_email"] == "asha.kumar@znova-demo.example"
    assert body["employment_status"] == "Active"
    assert body["is_active"] is True
    assert body["manager_id"] is None


def test_employee_ids_increase(client):
    assert create(client, "Asha")["employee_id"] == "EMP-0001"
    assert create(client, "Bala")["employee_id"] == "EMP-0002"


def test_create_duplicate_email_returns_409(client):
    create(client, "Asha", last="Kumar")
    response = client.post(BASE, json=payload())
    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "CONFLICT"
    assert error["request_id"]


def test_create_invalid_email_returns_422(client):
    response = client.post(BASE, json=payload(work_email="not-an-email"))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert error_fields(response) == ["work_email"]


def test_create_empty_name_returns_422(client):
    response = client.post(BASE, json=payload(first_name="   "))
    assert response.status_code == 422
    assert error_fields(response) == ["first_name"]


def test_create_future_hire_date_returns_422(client):
    response = client.post(BASE, json=payload(hire_date="2026-10-01"))
    assert response.status_code == 422
    assert error_fields(response) == ["hire_date"]


def test_hire_date_on_demo_today_is_allowed(client):
    response = client.post(BASE, json=payload(hire_date="2026-09-30"))
    assert response.status_code == 201


def test_create_missing_required_field_returns_422(client):
    body = payload()
    del body["department_id"]
    response = client.post(BASE, json=body)
    assert response.status_code == 422
    assert "department_id" in error_fields(response)


def test_create_bad_work_mode_returns_422(client):
    response = client.post(BASE, json=payload(work_mode="Teleport"))
    assert response.status_code == 422
    assert error_fields(response) == ["work_mode"]


def test_create_unknown_department_returns_422(client):
    response = client.post(BASE, json=payload(department_id="D99"))
    assert response.status_code == 422
    assert error_fields(response) == ["department_id"]


def test_create_unknown_manager_returns_422(client):
    response = client.post(BASE, json=payload(manager_id="EMP-9999"))
    assert response.status_code == 422
    assert error_fields(response) == ["manager_id"]


# ---------- read one ----------

def test_get_employee(client):
    created = create(client, "Asha")
    response = client.get(f"{BASE}/{created['employee_id']}")
    assert response.status_code == 200
    assert response.json()["full_name"] == "Asha Nair"


def test_get_missing_employee_returns_404(client):
    response = client.get(f"{BASE}/EMP-9999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


# ---------- update ----------

def test_patch_changes_only_sent_fields(client):
    created = create(client, "Asha")
    response = client.patch(
        f"{BASE}/{created['employee_id']}", json={"work_location": "Pune"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["work_location"] == "Pune"
    assert body["full_name"] == "Asha Nair"
    assert body["work_mode"] == "Hybrid"


def test_patch_name_updates_full_name(client):
    created = create(client, "Asha")
    response = client.patch(f"{BASE}/{created['employee_id']}", json={"last_name": "Menon"})
    assert response.json()["full_name"] == "Asha Menon"


def test_patch_with_empty_body_changes_nothing(client):
    created = create(client, "Asha")
    response = client.patch(f"{BASE}/{created['employee_id']}", json={})
    assert response.status_code == 200
    assert response.json()["work_email"] == created["work_email"]


def test_patch_duplicate_email_returns_409(client):
    create(client, "Asha")
    second = create(client, "Bala")
    response = client.patch(
        f"{BASE}/{second['employee_id']}", json={"work_email": "asha.nair@znova-demo.example"}
    )
    assert response.status_code == 409


def test_patch_keeping_own_email_is_allowed(client):
    created = create(client, "Asha")
    response = client.patch(
        f"{BASE}/{created['employee_id']}", json={"work_email": created["work_email"]}
    )
    assert response.status_code == 200


def test_patch_invalid_email_returns_422(client):
    created = create(client, "Asha")
    response = client.patch(f"{BASE}/{created['employee_id']}", json={"work_email": "bad"})
    assert response.status_code == 422
    assert error_fields(response) == ["work_email"]


def test_patch_missing_employee_returns_404(client):
    response = client.patch(f"{BASE}/EMP-9999", json={"work_location": "Pune"})
    assert response.status_code == 404


def test_patch_manager_cannot_be_self(client):
    created = create(client, "Asha")
    response = client.patch(
        f"{BASE}/{created['employee_id']}", json={"manager_id": created["employee_id"]}
    )
    assert response.status_code == 422
    assert error_fields(response) == ["manager_id"]


def test_patch_null_for_required_field_returns_422(client):
    created = create(client, "Asha")
    response = client.patch(f"{BASE}/{created['employee_id']}", json={"work_mode": None})
    assert response.status_code == 422
    assert error_fields(response) == ["work_mode"]


def test_patch_exit_date_before_hire_date_returns_422(client):
    created = create(client, "Asha", hire_date="2024-06-03")
    response = client.patch(
        f"{BASE}/{created['employee_id']}", json={"exit_date": "2024-01-01"}
    )
    assert response.status_code == 422
    assert error_fields(response) == ["exit_date"]


def test_patch_status_updates_is_active(client):
    created = create(client, "Asha")
    response = client.patch(
        f"{BASE}/{created['employee_id']}",
        json={"employment_status": "Resigned", "exit_date": "2026-09-01"},
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False


# ---------- delete (soft) ----------

def test_delete_is_soft(client):
    created = create(client, "Asha")
    employee_id = created["employee_id"]
    assert client.delete(f"{BASE}/{employee_id}").status_code == 204
    still_there = client.get(f"{BASE}/{employee_id}")
    assert still_there.status_code == 200
    assert still_there.json()["is_active"] is False


def test_deleted_employee_is_found_with_is_active_filter(client):
    create(client, "Asha")
    gone = create(client, "Bala")
    client.delete(f"{BASE}/{gone['employee_id']}")
    inactive = client.get(BASE, params={"is_active": False}).json()
    assert [e["employee_id"] for e in inactive["items"]] == [gone["employee_id"]]
    active = client.get(BASE, params={"is_active": True}).json()
    assert active["total"] == 1


def test_delete_missing_employee_returns_404(client):
    assert client.delete(f"{BASE}/EMP-9999").status_code == 404


# ---------- list: pagination, filters, search, sort ----------

def test_list_pagination_shape(client):
    seed_five(client)
    body = client.get(BASE, params={"page": 1, "size": 2}).json()
    assert len(body["items"]) == 2
    assert (body["total"], body["page"], body["size"], body["pages"]) == (5, 1, 2, 3)


def test_list_last_page_has_remaining_items(client):
    seed_five(client)
    body = client.get(BASE, params={"page": 3, "size": 2}).json()
    assert len(body["items"]) == 1
    assert body["items"][0]["employee_id"] == "EMP-0005"


def test_list_page_beyond_end_is_empty_but_keeps_total(client):
    seed_five(client)
    body = client.get(BASE, params={"page": 9, "size": 2}).json()
    assert body["items"] == []
    assert body["total"] == 5


def test_list_defaults(client):
    seed_five(client)
    body = client.get(BASE).json()
    assert (body["page"], body["size"], body["total"]) == (1, 20, 5)


def test_list_filter_by_department(client):
    seed_five(client)
    body = client.get(BASE, params={"department_id": "D02"}).json()
    assert body["total"] == 2


def test_list_filter_by_role_and_work_mode_and_status(client):
    seed_five(client)
    assert client.get(BASE, params={"role_id": "R010"}).json()["total"] == 2
    assert client.get(BASE, params={"work_mode": "Remote"}).json()["total"] == 1
    assert client.get(BASE, params={"employment_status": "Active"}).json()["total"] == 5
    assert client.get(BASE, params={"employment_status": "Resigned"}).json()["total"] == 0


def test_list_filter_by_manager(client):
    a = seed_five(client)
    body = client.get(BASE, params={"manager_id": a["employee_id"]}).json()
    assert body["total"] == 2


def test_list_filter_by_hire_date_range(client):
    seed_five(client)
    body = client.get(
        BASE, params={"hire_date_from": "2021-01-01", "hire_date_to": "2024-12-31"}
    ).json()
    assert body["total"] == 3  # Asha 2024, Bala 2021, Divya 2023


def test_list_search_by_name_is_case_insensitive(client):
    seed_five(client)
    body = client.get(BASE, params={"q": "BALA"}).json()
    assert [e["full_name"] for e in body["items"]] == ["Bala Nair"]


def test_list_search_by_email(client):
    seed_five(client)
    body = client.get(BASE, params={"q": "charu.nair@"}).json()
    assert body["total"] == 1


def test_list_filters_and_pagination_work_together(client):
    seed_five(client)
    body = client.get(
        BASE,
        params={"department_id": "D01", "work_location": "Chennai", "size": 1, "page": 2},
    ).json()
    assert body["total"] == 2  # Asha and Esha
    assert len(body["items"]) == 1
    assert body["pages"] == 2


def test_list_filter_and_search_combined(client):
    seed_five(client)
    body = client.get(BASE, params={"department_id": "D02", "q": "div"}).json()
    assert [e["full_name"] for e in body["items"]] == ["Divya Nair"]


def test_list_sort_descending_by_hire_date(client):
    seed_five(client)
    body = client.get(BASE, params={"sort": "-hire_date"}).json()
    assert body["items"][0]["full_name"] == "Esha Nair"
    assert body["items"][-1]["full_name"] == "Charu Nair"


def test_list_sort_by_name(client):
    seed_five(client)
    body = client.get(BASE, params={"sort": "full_name"}).json()
    assert body["items"][0]["full_name"] == "Asha Nair"


def test_list_invalid_sort_returns_422(client):
    response = client.get(BASE, params={"sort": "salary"})
    assert response.status_code == 422
    assert error_fields(response) == ["sort"]


def test_list_invalid_paging_returns_422(client):
    assert client.get(BASE, params={"size": 0}).status_code == 422
    assert client.get(BASE, params={"size": 101}).status_code == 422
    assert client.get(BASE, params={"page": 0}).status_code == 422


def test_list_empty_database(client):
    body = client.get(BASE).json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["pages"] == 0


# ---------- team ----------

def test_team_returns_direct_reports(client):
    manager = seed_five(client)
    response = client.get(f"{BASE}/{manager['employee_id']}/team")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert {e["full_name"] for e in body["items"]} == {"Bala Nair", "Divya Nair"}


def test_team_of_employee_without_reports_is_empty(client):
    seed_five(client)
    body = client.get(f"{BASE}/EMP-0005/team").json()
    assert body["items"] == []
    assert body["total"] == 0


def test_team_of_missing_employee_returns_404(client):
    assert client.get(f"{BASE}/EMP-9999/team").status_code == 404