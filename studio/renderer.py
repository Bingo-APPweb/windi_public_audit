from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import os

BASE_DIR = "/opt/windi/studio/templates/db"

def render_procurement_form(data: dict, output_path: str):
    env = Environment(loader=FileSystemLoader(os.path.join(BASE_DIR, "layouts")))
    template = env.get_template("procurement_form.html")
    html_content = template.render(data)

    HTML(
        string=html_content,
        base_url=BASE_DIR
    ).write_pdf(output_path)

    print(f"PDF gerado em {output_path}")
