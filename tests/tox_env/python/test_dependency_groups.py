from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from packaging.requirements import Requirement

from tox.tox_env.errors import Fail
from tox.tox_env.python.dependency_groups import resolve

if TYPE_CHECKING:
    from typing import Final

    from tox.pytest import ToxProjectCreator


@pytest.mark.parametrize(
    ("project_name", "requirement_name", "extra_name", "requested_extra"),
    [
        pytest.param("demo-pkg", "demo-pkg", "extra_1", "extra-1", id="extra-key"),
        pytest.param("demo-pkg", "demo_pkg", "extra-1", "extra-1", id="requirement-name"),
        pytest.param("Demo_Pkg", "demo-pkg", "extra-1", "extra-1", id="project-name"),
        pytest.param("demo-pkg", "demo-pkg", "extra-1", "EXTRA_1", id="requested-extra"),
        pytest.param("Demo._Pkg", "DEMO--PKG", "Extra._1", "EXTRA--1", id="mixed-separators"),
    ],
)
def test_resolve_extra_names(
    tox_project: ToxProjectCreator,
    project_name: str,
    requirement_name: str,
    extra_name: str,
    requested_extra: str,
) -> None:
    project: Final = tox_project({
        "pyproject.toml": f"""
            [project]
            name = "{project_name}"
            [project.optional-dependencies]
            "{extra_name}" = ["extra-pkg>=1.0"]
            [dependency-groups]
            test = ["{requirement_name}[{requested_extra}]", "other-pkg[EXTRA_1]>=2"]
        """,
    })
    assert resolve(project.path, {"test"}) == {Requirement("extra-pkg>=1.0"), Requirement("other-pkg[EXTRA_1]>=2")}


def test_resolve_nested_extra_names(tox_project: ToxProjectCreator) -> None:
    project: Final = tox_project({
        "pyproject.toml": """
            [project]
            name = "Demo_Pkg"
            [project.optional-dependencies]
            Extra_1 = ["first>=1", "DEMO.PKG[Extra_2]"]
            Extra_2 = ["second>=2", "demo--pkg[EXTRA.1]"]
            [dependency-groups]
            test = ["demo-pkg[extra-1,EXTRA_2]"]
        """,
    })
    assert resolve(project.path, {"test"}) == {Requirement("first>=1"), Requirement("second>=2")}


@pytest.mark.parametrize(
    ("requirements", "message"),
    [
        pytest.param('["demo_pkg[missing]"]', "extra 'missing' not found", id="missing-extra"),
        pytest.param('["not a requirement"]', "'not a requirement' is not valid requirement", id="invalid-requirement"),
    ],
)
def test_resolve_extra_errors(tox_project: ToxProjectCreator, requirements: str, message: str) -> None:
    project: Final = tox_project({
        "pyproject.toml": f"""
            [project]
            name = "demo-pkg"
            [project.optional-dependencies]
            Extra_1 = {requirements}
            [dependency-groups]
            test = ["DEMO_PKG[extra-1]"]
        """,
    })
    with pytest.raises(Fail, match=message):
        resolve(project.path, {"test"})
