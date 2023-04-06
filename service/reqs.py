"""
This module defines methods for fetching the content of a requirements.txt file from GitHub.

Eventually, the goal is to build this functionality into pangeo-forge-runner, at which point this
module can be deleted.

https://github.com/pangeo-forge/pangeo-forge-runner/issues/27 tracks this development.
"""

import base64

from pydantic import BaseModel, validator
from gidgethub.httpx import GitHubAPI

from .payloads import PullRequest


class GitContent(BaseModel):
    content: str
    encoding: str

    @validator("encoding")
    def verify_encoding(cls, v: str):
        if not v.strip() == "base64":
            raise ValueError(f"Encoding '{v}' is not 'base64'")
        return v
    
    @property
    def decoded_content(self) -> str:
        return base64.b64decode(self.content)


class GitTreeItem(BaseModel):
    path: str
    url: str


class GitTree(BaseModel):
    tree: list[GitTreeItem]

    @property
    def requirements_file(self) -> GitTreeItem | None:
        matching = [i for i in self.tree if i.path.endswith("requirements.txt")]
        if len(matching) > 1:
            raise ValueError(f"Git tree {self.tree} contains > 1 requirements.txt.")
        return matching.pop(0) if matching else None


async def get_reqs_from_github(pr: PullRequest, gh: GitHubAPI) -> list:
    tree_response = await gh.getitem(pr.head.repo.trees_url + "?recursive=1")
    tree = GitTree(**tree_response)
    reqs = []
    if tree.requirements_file:
        reqs_content_response = await gh.getitem(tree.requirements_file.url)
        reqs_content = GitContent(**reqs_content_response)
        reqs = [line.strip() for line in reqs_content.decoded_content]
    return reqs
