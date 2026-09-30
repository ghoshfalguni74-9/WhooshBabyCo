from pathlib import Path

from admin.database import create_login_table, create_users_table, get_user_by_email, list_logins, save_login, update_user_details


def test_login_database_stores_records(tmp_path):
    db_path = tmp_path / "login_database.db"

    create_login_table(db_path)
    save_login("admin", "secret123", db_path)

    records = list_logins(db_path)

    assert len(records) == 1
    assert records[0]["username"] == "admin"
    assert records[0]["password"] == "secret123"


def test_admin_data_folder_is_created():
    admin_dir = Path(__file__).resolve().parents[1] / "admin" / "data"
    assert admin_dir.exists(), "Admin data folder should exist"


def test_user_details_can_be_updated(tmp_path):
    db_path = tmp_path / "profile.db"
    create_users_table(db_path)
    from admin.database import create_user_account

    create_user_account({
        "name": "Asha", "dob": "2020-01-01", "gender": "Female", "email": "asha@example.com",
        "phone": "1234567890", "password": "StrongPass1!",
    }, db_path)
    assert update_user_details("asha@example.com", {"name": "Asha Rao", "dob": "2020-01-01", "gender": "Female", "phone": "9999999999"}, db_path)
    assert get_user_by_email("asha@example.com", db_path)["name"] == "Asha Rao"
