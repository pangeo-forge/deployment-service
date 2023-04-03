from fastapi import BackgroundTasks
from gidgethub.httpx import GitHubAPI

from .payloads import PullRequestPayload


async def test_deploy(
    pr: PullRequestPayload,
    gh: GitHubAPI,
    background_tasks: BackgroundTasks,      
):
    ...


LABEL_HANDLERS = {
    "test-deploy": test_deploy,
}
