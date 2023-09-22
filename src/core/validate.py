from lcacollect_config.context import get_token
from lcacollect_config.exceptions import DatabaseItemNotFound
from strawberry.types import Info


async def authenticate_project(info: Info, project_id: str):
    """Checks that project exists and user has access to it"""
    from lcacollect_config.validate import project_exists

    project = await project_exists(project_id=project_id, token=get_token(info))
    if not project:
        raise DatabaseItemNotFound(f"Project with id: {project_id} does not exist")
    return project
