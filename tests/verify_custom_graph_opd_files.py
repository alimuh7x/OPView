import sys
import tempfile
import types
from pathlib import Path

from data.sources import GenericTextDataSource
from ui.graphs import get_textdata_files


def main():
    with tempfile.TemporaryDirectory() as tmp:
        textdata_dir = Path(tmp) / "ProjectA" / "TextData"
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
        sys.modules["OPView"] = fake_opview

        print(f"[verify][custom-graph-opd] input opd_file={opd_file}", flush=True)
        files = get_textdata_files(["ProjectA/TextData"])
        print(f"[verify][custom-graph-opd] discovered files={files}", flush=True)

        source = GenericTextDataSource(opd_file)
        loaded = source.load()
        print(f"[verify][custom-graph-opd] load result={loaded}", flush=True)
        print(f"[verify][custom-graph-opd] columns={source.get_available_columns() if loaded else []}", flush=True)


if __name__ == "__main__":
    main()
