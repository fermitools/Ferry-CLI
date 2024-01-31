# __init__.py
try:
    from ferry_cli.helpers.supported_workflows.CloneResource import CloneResource
    from ferry_cli.helpers.supported_workflows.GetFilteredGroupInfo import GetFilteredGroupInfo
except ImportError:
    from helpers.supported_workflows.CloneResource import CloneResource
    from helpers.supported_workflows.GetFilteredGroupInfo import GetFilteredGroupInfo


SUPPORTED_WORKFLOWS = {
    "cloneResource": CloneResource,
    "getFilteredGroupInfo": GetFilteredGroupInfo,
}
