from flask import Flask

import openapi


def make_app():
    app = Flask(__name__)

    @app.route("/api/thing/<int:thing_id>")
    def thing(thing_id):
        """One thing."""

    @app.route("/api/compare")
    def compare():
        """Two things."""

    @app.route("/not-api")
    def page():
        """A page."""

    assert openapi.register(app, {"API_DOCS": "true"})
    return app


def test_spec_lists_api_routes_with_typed_path_and_query_arguments():
    paths = openapi.build_spec(make_app())["paths"]
    assert set(paths) == {"/api/thing/{thing_id}", "/api/compare"}
    get = paths["/api/thing/{thing_id}"]["get"]
    assert get["summary"] == "One thing."
    assert get["parameters"] == [{"name": "thing_id", "in": "path", "required": True, "schema": {"type": "integer"}}]
    assert [p["name"] for p in paths["/api/compare"]["get"]["parameters"]] == ["kind", "a", "b", "terms"]


def test_docs_page_loads_its_files_locally():
    c = make_app().test_client()
    assert c.get("/api/docs/").status_code == 200
    js = c.get("/api/docs/swagger-initializer.js").get_data(as_text=True)
    assert '"/api/openapi.json"' in js


def test_docs_are_off_when_api_docs_is_missing_or_not_true():
    for env in ({}, {"API_DOCS": "false"}, {"API_DOCS": ""}, {"API_DOCS": "1"}):
        app = Flask(__name__)
        assert openapi.register(app, env) is False
        c = app.test_client()
        assert c.get("/api/openapi.json").status_code == 404
        assert c.get("/api/docs/").status_code == 404


def test_docs_are_on_only_for_the_value_true():
    assert openapi.enabled({"API_DOCS": "true"})
    assert openapi.enabled({"API_DOCS": " TRUE "})
    assert not openapi.enabled({"API_DOCS": "yes"})
