from __future__ import annotations

from importlib.metadata import entry_points

import full_stack_athlete

CLI_TARGET = "full_stack_athlete.cli:app"


def test_package_has_version() -> None:
    assert full_stack_athlete.__version__ == "0.1.0"


def test_console_scripts_point_at_the_cli() -> None:
    scripts = {
        ep.name: ep.value
        for ep in entry_points(group="console_scripts")
        if ep.value.startswith("full_stack_athlete.")
    }

    assert scripts == {"full-stack-athlete": CLI_TARGET, "fsa": CLI_TARGET}
