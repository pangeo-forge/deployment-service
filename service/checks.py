from gidgethub.httpx import GitHubAPI

from .agents import Agent
from .payloads import PullRequest


def check_run(handler):
    async def wrapper(pr: PullRequest, gh: GitHubAPI, agent: Agent):
        # TODO: make in-progress check run
        try:
            await handler(pr, gh, agent)
        except Exception as e:
            # TODO: update check run as failed
            raise e

        # TODO: update check run as succeeded

    return wrapper
