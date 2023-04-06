import asyncio

from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx


async def async_check_output(cmd: str):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    return stdout.decode("utf-8").strip()


class Agent(ABC):

    @abstractmethod
    async def check_output(self, cmd: list[str], pkgs: list[str]) -> str:
        """Invoke the provided `pangeo-forge-runner` `cmd` on the agent, while first installing
        any specified packages, and return `stdout`."""
        # NOTE: Argument `pkgs` is temporary. See docstring at top of `.reqs` module.
        # FIXME: Instead of returning the full `stdout`, should we parse this at the agent layer
        # and return a structured JSON response conveying the result of the invocation? This will 
        # require coordination with the agent repositories, and highlights the importance of
        # defining the REST communication models for these repos in a central location.


@dataclass
class GCPCloudRunAgent:

    service_url: str
    invoker_keyfile: str
    env: str = "notebook"

    async def get_invoker_token(self):
        await async_check_output(
            f"gcloud auth activate-service-account --key-file={self.invoker_keyfile}"
        )
        token = await async_check_output("gcloud auth print-identity-token")
        return token

    async def check_output(self, cmd: list[str], pkgs: list[str]) -> str:
        timeout = httpx.Timeout(connect=10.0, read=300.0, write=10.0, pool=10.0)
        token = await self.get_invoker_token()
        async with httpx.AsyncClient(timeout=timeout) as session:
            r = await session.post(
                self.service_url,
                json={
                    "pangeo_forge_runner": {"cmd": cmd},
                    # NOTE: `install` is temporary. See docstring at top of `.reqs` module.
                    "install": {"pkgs": pkgs, "env": self.env},
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            return r.json()["pangeo_forge_runner_result"]
