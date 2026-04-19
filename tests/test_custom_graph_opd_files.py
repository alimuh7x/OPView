import sys
import types

from ui.graphs import get_textdata_files


def test_custom_graph_discovers_opd_files(monkeypatch, tmp_path):
    textdata_dir = tmp_path / "ProjectA" / "TextData"
    textdata_dir.mkdir(parents=True)
    opd_file = textdata_dir / "sample.opd"
    opd_file.write_text("Time Value\n0 1\n1 2\n", encoding="utf-8")

    fake_opview = types.SimpleNamespace(
        app_context=None,
        discovered_project_folders={
            "ProjectA/TextData": {
                "has_textdata": True,
                "textdata_path": textdata_dir,
            }
        },
    )
    monkeypatch.setitem(sys.modules, "OPView", fake_opview)

    files = get_textdata_files(["ProjectA/TextData"])

    assert str(opd_file) in files
