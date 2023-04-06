import json
from pathlib import Path

import pytest

from ..payloads import PullRequestPayload


HERE = Path(__file__).parent


@pytest.mark.parametrize(
    "action, webhook_payload_path",
    [(p.stem, p.resolve()) for p in (HERE / "samples" / "events" / "pull_request").iterdir()]
)
def test_pull_request_model(action, webhook_payload_path):
    with open(webhook_payload_path) as f:
        j = json.load(f)

    # make sure json samples are named correctly
    assert action == j["action"]

    # parse json data to model
    pr = PullRequestPayload(**j)

    # make sure label field is parsed correctly
    if action == "labeled":
        assert pr.label is not None
        assert isinstance(pr.label, dict)
    else:
        assert pr.label is None

    # test derived label property
    assert isinstance(pr.event_label_names, list)
