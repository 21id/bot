from jinja2 import Environment, FileSystemLoader, select_autoescape


class TemplateRenderer:
    """Jinja2 Template Renderer."""

    def __init__(self, templates_dir: str):
        """Initialize renderer."""
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(),
        )

    def render(self, template_name: str, context: dict) -> str:
        """Render from template name and data."""
        template = self.env.get_template(template_name)

        return template.render(**context)
