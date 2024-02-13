# __init__.py
try:
    from ferry_cli.helpers.supported_workflows.CloneResource import CloneResource
    from ferry_cli.helpers.supported_workflows.GetFilteredGroupInfo import (
        GetFilteredGroupInfo,
    )
except ImportError:
    from helpers.supported_workflows.CloneResource import CloneResource  # type: ignore
    from helpers.supported_workflows.GetFilteredGroupInfo import GetFilteredGroupInfo  # type: ignore


SUPPORTED_WORKFLOWS = {
    "cloneResource": CloneResource,
    "getFilteredGroupInfo": GetFilteredGroupInfo,
}
