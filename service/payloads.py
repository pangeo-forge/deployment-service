from pydantic import BaseModel


class GitHubWebhookPayload(BaseModel):
    sender: dict


class PullRequestPayload(GitHubWebhookPayload):
    pull_request: dict
    label: dict | None

    @property
    def event_labels(self):
        """Labels for which we should consider taking action for this event."""
        return [self.label] if self.label else [l for l in self.pull_request["labels"]]

    @property
    def event_label_names(self):
        """Names of labels for which we should consider taking action."""
        return [l["name"] for l in self.event_labels]
