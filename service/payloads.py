from pydantic import BaseModel


class GitHubWebhookPayload(BaseModel):
    sender: dict


class Repo(BaseModel):
    html_url: str
    contents_url: str
    trees_url: str    


class Head(BaseModel):
    sha: str
    repo: Repo


class PullRequest(BaseModel):
    head: Head
    labels: list


class PullRequestPayload(GitHubWebhookPayload):
    pull_request: PullRequest
    label: dict | None

    @property
    def event_labels(self):
        """Labels for which we should consider taking action for this event."""
        return [self.label] if self.label else [l for l in self.pull_request.labels]

    @property
    def event_label_names(self):
        """Names of labels for which we should consider taking action."""
        return [l["name"] for l in self.event_labels]
