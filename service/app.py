import os

import httpx
from fastapi import BackgroundTasks, FastAPI, Request, status
from gidgethub.apps import get_installation_access_token
from gidgethub.httpx import GitHubAPI
from gidgethub.sansio import Event as GitHubEvent
from gidgethub.routing import Router as GitHubEventRouter
from pydantic import BaseModel, SecretStr

from .handlers import LABEL_HANDLERS
from .payloads import PullRequestPayload

app = FastAPI()
event_router = GitHubEventRouter()


class Config(BaseModel):
    app_name: str
    app_id: int
    webhook_secret: SecretStr
    private_key: SecretStr


def get_config():
    return Config(
        app_name=os.environ["GITHUB_APP_NAME"],
        app_id=os.environ["GITHUB_APP_ID"],
        webhook_secret=os.environ["GITHUB_WEBHOOK_SECRET"],
        private_key=os.environ["GITHUB_APP_PRIVATE_KEY"],
    )


async def get_authenticated_github_session(installation_id: int) -> GitHubAPI:
    """Get an async GitHub client authenticated for the given installation."""

    httpx_async_client = httpx.AsyncClient()
    c = get_config()
    gh = GitHubAPI(httpx_async_client, c.app_name)
    token_response = await get_installation_access_token(
        gh,
        installation_id=installation_id,
        app_id=c.app_id,
        private_key=c.private_key.get_secret_value(),
    )
    return GitHubAPI(httpx_async_client, c.app_name, oauth_token=token_response["token"])


@app.post(
    "/github/hooks/",
    status_code=status.HTTP_200_OK,
    summary="Endpoint to which GitHub posts webhooks.",
)
async def receive_github_hook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    payload_bytes = await request.body()
    # GitHubEvent.from_http handles hash signature validation for us. GitHub docs:
    # https://docs.github.com/en/developers/webhooks-and-events/webhooks/securing-your-webhooks#validating-payloads-from-github
    event = GitHubEvent.from_http(
        {k.lower(): v for k, v in request.headers.items()},
        payload_bytes,
        secret=get_config().webhook_secret.get_secret_value(),
    )
    gh = get_authenticated_github_session(event.data["installation"]["id"])
    await event_router.dispatch(event, gh=gh, background_tasks=background_tasks)


@event_router.register("pull_request", action="opened")
@event_router.register("pull_request", action="reopened")
@event_router.register("pull_request", action="synchronize")
@event_router.register("pull_request", action="labeled")
async def dispatch_labeled_pull_request_handler(
    event: GitHubEvent,
    gh: GitHubAPI,
    background_tasks: BackgroundTasks,
):
    """For a labeled pull request, dispatch the label handler if it exists."""

    pr = PullRequestPayload(**event.data)
    actionable_labels = [l for l in pr.event_label_names if l in LABEL_HANDLERS]
    for label in actionable_labels:
        await LABEL_HANDLERS[label](pr, gh, background_tasks)
