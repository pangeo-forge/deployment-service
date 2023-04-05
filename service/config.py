from pydantic import BaseModel, BaseSettings, Field, PyObject, SecretStr, validator

from .agents import Agent


class GitHubAppConfig(BaseModel):
    name: str
    id: int
    webhook_secret: SecretStr
    private_key: SecretStr


class AgentConfig(BaseModel):
    cls: PyObject = Field(
        ...,
        description="""
        The agent class. Must be a subclass of the abstract base class `services.agents.Agent`.
        """
    )
    service_url: str = Field(..., description="URL at which the agent service is deployed.")
    invoker_keyfile: str | None = Field(
        None,
        description="""
        If applicable, a keyfile which grants permission to invoke the agent service.
        """
    )


class Config(BaseSettings):
    """This class is automatically instantiated from the environment.
    Double underscores are used to delimit subfields. The env must
    therefore include the following required variables:

    ```
    GITHUB_APP__NAME=
    GITHUB_APP__ID=
    GITHUB_APP__WEBHOOK_SECRET=
    GITHUB_APP__PRIVATE_KEY=
    AGENT__CLS=
    AGENT__SERVICE_URL=
    ```

    And, depending on the value passed for `AGENT__CLS` may also need to set:

    ```
    AGENT__INVOKER_KEYFILE=
    ```

    For detailed description of each variable, see corresponding submodel
    (`GitHubAppConfig` or `AgentConfig`).
    """
    github_app: GitHubAppConfig= Field(
        ...,
        description="""
        Config details of the GitHub App instance.
        """
    )
    agent: AgentConfig = Field(
        ...,
        description="""
        Config for the bakery Agent. Note that while the user passes an `AgentConfig` object,
        the `.agent` attribute of the instantiated class is not an `AgentConfig` object, but
        rather an instance of the provided `AgentConfig.cls`.
        """
    )

    @validator("agent")
    def parse_agent(cls, v: AgentConfig) -> Agent:
        """Parses the input `AgentConfig` into the specified `Agent` type."""
        kws = v.dict(exclude={"cls"}, exclude_none=True)
        return v.cls(**kws)

    class Config:
        env_nested_delimiter = '__'
