from functools import lru_cache
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, Request, status
from gidgethub.apps import get_installation_access_token
from gidgethub.httpx import GitHubAPI
from gidgethub.sansio import Event as GitHubEvent
from gidgethub.routing import Router as GitHubEventRouter

from .agents import Agent
from .config import Config, GitHubAppConfig
from .handlers import LABEL_HANDLERS
from .payloads import PullRequestPayload

app = FastAPI()
event_router = GitHubEventRouter()


@lru_cache
def get_config():
    return Config()


async def get_authenticated_github_session(
    installation_id: int,
    github_app: GitHubAppConfig,
) -> GitHubAPI:
    """Get an async GitHub client authenticated for the given installation."""

    httpx_async_client = httpx.AsyncClient()
    gh = GitHubAPI(httpx_async_client, github_app.name)
    token_response = await get_installation_access_token(
        gh,
        installation_id=installation_id,
        app_id=github_app.id,
        private_key=github_app.private_key.get_secret_value(),
    )
    return GitHubAPI(httpx_async_client, github_app.name, oauth_token=token_response["token"])


@app.post(
    "/github/hooks/",
    status_code=status.HTTP_200_OK,
    summary="Endpoint to which GitHub posts webhooks.",
)
async def receive_github_hook(
    request: Request,
    c: Annotated[Config, Depends(get_config)]
):
    payload_bytes = await request.body()
    # GitHubEvent.from_http handles hash signature validation. GitHub docs:
    # https://docs.github.com/en/developers/webhooks-and-events/webhooks/securing-your-webhooks#validating-payloads-from-github
    event = GitHubEvent.from_http(
        {k.lower(): v for k, v in request.headers.items()},
        payload_bytes,
        secret=c.github_app.webhook_secret.get_secret_value(),
    )
    gh = get_authenticated_github_session(event.data["installation"]["id"], c.github_app)
    await event_router.dispatch(event, gh=gh, agent=c.agent)


@event_router.register("pull_request", action="opened")
@event_router.register("pull_request", action="reopened")
@event_router.register("pull_request", action="synchronize")
@event_router.register("pull_request", action="labeled")
async def dispatch_labeled_pull_request_handler(event: GitHubEvent, gh: GitHubAPI, agent: Agent):
    """For a labeled pull request, dispatch the label handler if it exists."""

    pr = PullRequestPayload(**event.data)
    actionable_labels = [l for l in pr.event_label_names if l in LABEL_HANDLERS]
    for label in actionable_labels:
        await LABEL_HANDLERS[label](pr, gh, agent)
