import database

def test_create_get_update(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    row=database.create_inquiry("Test Person","test@example.test","Billing","Question about invoice","Invoice question","Medium","Draft")
    assert row["id"] == 1
    assert database.get_inquiry(1)["patient_name"] == "Test Person"
    assert database.update_inquiry(1,status="Resolved",priority="Low")
    updated=database.get_inquiry(1)
    assert updated["status"] == "Resolved"
    assert updated["priority"] == "Low"
