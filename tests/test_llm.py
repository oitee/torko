import pytest

import llm


class _Resp:
    def __init__(self, status, data=None):
        self.status_code, self._data, self.text = status, data, ""

    def json(self):
        return self._data


def test_generate_sends_the_schema_and_reads_the_answer_without_thoughts(monkeypatch):
    sent = {}

    def post(url, json, headers, timeout):
        sent.update(json)
        return _Resp(200, {"candidates": [{"content": {"parts": [{"text": "x", "thought": True}, {"text": '{"a": 1}'}]}}],
                           "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 2}})

    monkeypatch.setattr(llm.requests, "post", post)
    answer, tokens = llm.generate("m", "system", "body", "key", {"type": "object"})
    assert answer == {"a": 1}
    assert tokens == {"input": 5, "output": 2, "thinking": None}
    assert sent["generationConfig"]["responseJsonSchema"] == {"type": "object"}


def test_generate_raises_on_a_client_error(monkeypatch):
    monkeypatch.setattr(llm.requests, "post", lambda *a, **k: _Resp(400))
    with pytest.raises(llm.ApiError):
        llm.generate("m", "s", "b", "k", {})
