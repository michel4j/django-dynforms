import re

import yaml
from django.core.management.base import BaseCommand, CommandError


def strip_outer_tags(svg_text):
    """
    Strips the outer HTML tags from the SVG text.
    """

    pattern = r'^\s*<svg[^>]*>(.*)</svg>\s*$'
    return re.sub(r'\s+', ' ', re.sub(pattern, r'\1', svg_text, flags=re.DOTALL).strip())


class Command(BaseCommand):
    help = "Add an icon the icons.yml file for an App"

    def add_arguments(self, parser):
        parser.add_argument("icon_name", type=str)
        parser.add_argument(
            "icon_path", type=str, help="Path to the icon file"
        )

    def handle(self, *args, **options):

        with open(options['icon_path'], 'r', encoding="utf-8") as file:
            icon_content = file.read()

        app_icons = {options['icon_name']: strip_outer_tags(icon_content)}
        self.stdout.write(
            yaml.dump(app_icons, default_flow_style=False, allow_unicode=True, sort_keys=False, default_style='>')
        )


