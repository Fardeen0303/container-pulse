import pytest
import monitor.db as db


@pytest.fixture(autouse=True)
def use_temp_db(tmp_path):
    db.DB_PATH = str(tmp_path / "test.db")
    db.init_db()


def test_record_and_fetch_event():
    db.record_event("nginx-container", "restarted", 1)
    incidents = db.get_recent_incidents()
    assert len(incidents) == 1
    assert incidents[0]["container"] == "nginx-container"
    assert incidents[0]["event"] == "restarted"
    assert incidents[0]["attempt"] == 1


def test_get_restart_counts():
    db.record_event("nginx-container", "restarted", 1)
    db.record_event("nginx-container", "restarted", 2)
    db.record_event("devops-container", "restarted", 1)
    counts = db.get_restart_counts()
    counts_map = {r["container"]: r["count"] for r in counts}
    assert counts_map["nginx-container"] == 2
    assert counts_map["devops-container"] == 1


def test_get_recent_incidents_limit():
    for i in range(10):
        db.record_event("devops-container", "restarted", i)
    assert len(db.get_recent_incidents(5)) == 5


def test_empty_db_returns_empty_lists():
    assert db.get_recent_incidents() == []
    assert db.get_restart_counts() == []
