from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).parent.parent / "app.py")


def test_app_runs():
    app = AppTest.from_file(APP).run()
    assert not app.exception


def test_every_area_and_measure():
    app = AppTest.from_file(APP).run()
    for area in ["District 1", "District 6", "All of Mableton"]:
        app.button_group(key="area").set_value(area).run()
        assert not app.exception
        assert app.header[0].value == area
    for measure in ["Limited English", "Age 65+", "No internet at home"]:
        app.button_group(key="measure").set_value(measure).run()
        assert not app.exception


def test_dark_mode_and_color_schemes():
    app = AppTest.from_file(APP).run()
    app.toggle(key="dark").set_value(True).run()
    assert not app.exception
    for scheme in ["Blue", "Purple", "Mableton green"]:
        app.selectbox(key="scheme").set_value(scheme).run()
        assert not app.exception
    app.toggle(key="dark").set_value(False).run()
    assert not app.exception


def test_summaries_cover_every_area():
    import json

    summaries = json.loads(
        (Path(APP).parent / "data" / "district-summaries.json").read_text("utf-8")
    )
    assert set(summaries["areas"]) == {"city", "1", "2", "3", "4", "5", "6"}
    for written in summaries["areas"].values():
        assert written["summary"] and written["ideas"]
