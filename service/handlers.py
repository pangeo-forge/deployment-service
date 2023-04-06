from gidgethub.httpx import GitHubAPI

from .agents import Agent
from .payloads import PullRequest

from pydantic import BaseModel


class GitTree(BaseModel):
    tree: list


async def get_reqs_from_github(pr: PullRequest, gh: GitHubAPI):
    tree_response = gh.getitem(
        "/repos/{owner}/{repo}/git/trees/{tree_sha}",
        url_vars={
            "owner": pr.head.repo.owner,
            "repo": pr.head.repo.name,
            "tree_sha": pr.head.sha,
        }
    )
    tree = GitTree(**tree_response)
    fnames = [f.name for f in tree.tree]
    if len([n.endswith("requirements.txt") for n in fnames]) != 1:
        raise ValueError(f"Git {tree = } does not contain only one requirements.txt.")
    reqs_content = gh.getitem(

    )
    # return [line.strip() for line in reqs_content.decode().splitlines()]
    return ["pangeo-forge-runner==0.7.1"]


async def test_deploy(pr: PullRequest, gh: GitHubAPI, agent: Agent):
    # NOTE: `pkgs` is temporary, and should be removed following resolution of
    # https://github.com/pangeo-forge/pangeo-forge-runner/issues/27, at which point 
    # `pangeo-forge-runner` will handle it's own dynamic dependencies.
    pkgs = await get_reqs_from_github(pr, gh)  
    
    cmd = [
        "bake",
        f"--repo={pr.head.repo.html_url}",
        f"--ref={pr.head.sha}",
        "--prune",
        "--json",
    ]
    stdout = await agent.check_output(cmd, )


LABEL_HANDLERS = {
    "test-deploy": test_deploy,
}
