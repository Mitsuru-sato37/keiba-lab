import subprocess
import sys


def test_domain_contracts_do_not_import_frameworks() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import importlib, sys; "
                "importlib.import_module('keiba_domain.identifiers'); "
                "importlib.import_module('keiba_domain.time_values'); "
                "print('fastapi' in sys.modules, 'sqlalchemy' in sys.modules)"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "False False"
