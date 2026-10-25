"""Smoke coverage for the package and server-rendering foundation."""

from flask import Flask, render_template

from password_reset_demo import create_app


def test_app_factory_renders_package_template() -> None:
    app = create_app()

    assert isinstance(app, Flask)
    with app.app_context():
        assert "<main>" in render_template("base.html")
