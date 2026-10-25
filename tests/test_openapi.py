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

    app.register_blueprint(openapi.bp)
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
