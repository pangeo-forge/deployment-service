from fastapi import BackgroundTasks, Response, status
from gidgethub.httpx import GitHubAPI

from .payloads import GitHubWebhookPayload, PullRequestPayload


def sender_has_permission(sender: dict, handler: str) -> bool:
    # TODO: allow custom callables to accept or reject sender
    return True


def check_permission(f):
    """Decorator to verify whether or not a given sender has permission to dispatch a particular
    label event.
    """
    async def wrapper(p: GitHubWebhookPayload, *args, **kws):
        if sender_has_permission(p.sender, f.__name__):
            return f(p, *args, **kws)
        else:
            return Response(
                content=(
                    f"{p.sender['name'] = } not authorized to to dispatch handler '{f.__name__}'",
                ),
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
    return wrapper


@check_permission
async def test_deploy(
    pr: PullRequestPayload,
    gh: GitHubAPI,
    background_tasks: BackgroundTasks,      
):
    ...


LABEL_HANDLERS = {
    "test-deploy": test_deploy,
}
