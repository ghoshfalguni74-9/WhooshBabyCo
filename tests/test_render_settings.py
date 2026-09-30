import importlib
import os
import sys
import unittest
from pathlib import Path


class RenderEnvSettingsTests(unittest.TestCase):
    def test_render_ignores_repo_env_for_database_settings(self):
        project_root = Path(__file__).resolve().parents[1]
        env_file = project_root / ".env"
        original = env_file.read_text(encoding="utf-8") if env_file.exists() else None

        try:
            env_file.write_text(
                "DB_HOST=stale.example.com\n"
                "DB_NAME=postgres\n"
                "DB_USER=postgres\n"
                "DB_PASSWORD=stale-secret\n",
                encoding="utf-8",
            )

            os.environ["RENDER"] = "true"
            for key in ["DATABASE_URL", "DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]:
                os.environ.pop(key, None)

            sys.modules.pop("whoosh_site.settings", None)
            settings = importlib.import_module("whoosh_site.settings")

            self.assertEqual(settings.DATABASES["default"]["ENGINE"], "django.db.backends.sqlite3")
        finally:
            if original is None:
                if env_file.exists():
                    env_file.unlink()
            else:
                env_file.write_text(original, encoding="utf-8")
            os.environ.pop("RENDER", None)
            for key in ["DATABASE_URL", "DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]:
                os.environ.pop(key, None)
            sys.modules.pop("whoosh_site.settings", None)
