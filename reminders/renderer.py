"""Template rendering for reminder emails."""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=True)


def render(template_name: str, context: dict) -> str:
    """Render a Jinja2 HTML template and return the rendered string."""
    template = _env.get_template(template_name)
    return template.render(**context)
