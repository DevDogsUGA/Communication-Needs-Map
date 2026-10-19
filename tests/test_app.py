from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).parent.parent / "app.py")


def test_app_runs():
    app = AppTest.from_file(APP).run()
    assert not app.exception
