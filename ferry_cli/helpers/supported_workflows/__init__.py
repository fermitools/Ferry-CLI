# __init__.py
from typing import Mapping, Type

try:
    from ferry_cli.helpers.workflows import Workflow
    from ferry_cli.helpers.supported_workflows.CloneResource import CloneResource
    from ferry_cli.helpers.supported_workflows.GetFilteredGroupInfo import (
        GetFilteredGroupInfo,
    )
    from ferry_cli.helpers.supported_workflows.NewCapabilitySet import NewCapabilitySet
except ImportError:
    from helpers.workflows import Workflow  # type: ignore
    from helpers.supported_workflows.CloneResource import CloneResource  # type: ignore
    from helpers.supported_workflows.GetFilteredGroupInfo import GetFilteredGroupInfo  # type: ignore
    from helpers.supported_workflows.NewCapabilitySet import NewCapabilitySet  # type: ignore


SUPPORTED_WORKFLOWS: Mapping[str, Type[Workflow]] = {
    "cloneResource": CloneResource,
    "getFilteredGroupInfo": GetFilteredGroupInfo,
    "newCapabilitySet": NewCapabilitySet,
}
