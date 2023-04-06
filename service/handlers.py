from gidgethub.httpx import GitHubAPI

from .agents import Agent
from .checks import check_run
from .payloads import PullRequest
from .reqs import get_reqs_from_github


@check_run
async def test_deploy(pr: PullRequest, gh: GitHubAPI, agent: Agent):
    # NOTE: `pkgs` is temporary. See docstring at top of `.reqs` module.
    pkgs = await get_reqs_from_github(pr, gh)
    cmd = [
        "bake",
        f"--repo={pr.head.repo.html_url}",
        f"--ref={pr.head.sha}",
        "--prune",
        "--json",
    ]
    stdout = await agent.check_output(cmd, pkgs)
    return stdout


LABEL_HANDLERS = {
    "test-deploy": test_deploy,
}
