from worker.jobs.webhooks import _sign_payload


def test_sign_payload_deterministic():
    sig1 = _sign_payload("secret", b"payload")
    sig2 = _sign_payload("secret", b"payload")
    assert sig1 == sig2
    assert len(sig1) == 64
