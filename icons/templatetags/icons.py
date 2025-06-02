import yaml
from django import template
from django.apps import apps
from django.contrib.staticfiles import finders
from django.utils.safestring import mark_safe

register = template.Library()

ICONS = {}


def load_icons():
    """
    Load the icons module to ensure that the icons are available in the template.
    This is necessary for the template tags to work correctly.
    """
    app_names = [app.name for app in apps.get_app_configs()]
    for app_name in app_names:
        result = finders.find(f'{app_name}/icons.yml')
        if result:
            with open(result, 'r') as file:
                icons = yaml.safe_load(file)
                ICONS.update(icons)


load_icons()

DEFAULT_ICON = ICONS.get(
    'default',
    (
        '<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" />'
        '<path d="M11 16l4 -1.5" /><path d="M10 10c-.5 -1 -2.5 -1 -3 0" /><path d="M17 10c-.5 -1 -2.5 -1 -3 0" />'
    )
)
SVG_ICON = (
    '<svg  xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"  stroke="currentColor" '
    'stroke-width="{stroke}" stroke-linecap="round"  stroke-linejoin="round" class="{css_class}">{drawing}</svg>'
)
SVG_USE_SPRITE = (
    '<svg class="{css_class}" aria-hidden="true" stroke-width="{stroke}" fill="none" stroke-linecap="round" '
    'stroke-linejoin="round" stroke="currentColor"><use href="#{name}"></use></svg>'
)
SVG_SPRITES = (
    '<svg xmlns="http://www.w3.org/2000/svg" style="display: none;">\n\t{sprites}\n</svg>'
)
SPRITE_TEMPLATE = (
    '<symbol id="{name}" viewBox="0 0 24 24" >{drawing}</symbol>'
)


class SpriteRegistry:
    """
    A registry to keep track of SVG icons used in the current request.
    This is used to render the SVG sprite definitions in the template.
    """
    registry = {}

    @classmethod
    def get_sprites(cls, path: str) -> set[str]:
        """
        Returns the set of sprites registered for the given path.

        :param path: The request path for which to retrieve the registered sprites.
        """
        return cls.registry.get(path, set())

    @classmethod
    def add_sprite(cls, path: str, name: str):
        """
        Registers a sprite for the given request.

        :param path: The request path for which to register the sprite.
        :param name: The name of the sprite to register.
        """
        if path not in cls.registry:
            cls.registry[path] = set()
        cls.registry[path].add(name)


@register.simple_tag(takes_context=True)
def svg_icon(context, name, size=None, stroke=None, styles=""):
    size = 'md' if not size else size
    stroke = 2 if not stroke else stroke
    svg = SVG_USE_SPRITE.format(
        name=name, stroke=stroke, drawing=ICONS.get(name, DEFAULT_ICON), css_class=f"icon-{size} {styles}".strip()
    )
    return mark_safe(svg)


@register.simple_tag(takes_context=True)
def svg_sprites(context):
    """
    Returns a list of SVG icons that have been registered in the context.
    This is used to render the SVG sprite definitions in the template.
    """

    sprites_content = '\n\t'.join([
        SPRITE_TEMPLATE.format(name=name, drawing=ICONS.get(name, DEFAULT_ICON)) for name in ICONS.keys()
    ])
    return mark_safe(SVG_SPRITES.format(sprites=sprites_content))


@register.simple_tag
def font_icon(name, size=None):
    size = 'md' if not size else size
    return mark_safe(f'<i class="ti-{name} icon-{size}"></i>')


@register.simple_tag(takes_context=True)
def tool_icon(context, **kwargs):
    tooltip = '' if not kwargs.get('tooltip') else 'title={kwargs["tooltip"]!r}'
    icon = svg_icon(context, name=kwargs.get("icon"), size=kwargs.get("size"), stroke=kwargs.get("stroke"))
    color = kwargs.get("color", "info")
    badge = kwargs.get("badge", None)
    label = kwargs.get("label", None)
    label_text = f'<small class="text-nowrap d-none d-md-inline-block text-secondary mt-1">{label}</small>' if label else ''
    badge_text = (
        '' if not badge else
        f'<span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-{color}">{badge}</span>'
    )
    return mark_safe(
        f'<div class="d-flex flex-column align-items-center justify-content-center p-1" {tooltip}>'
        f'{icon}{badge_text}{label_text}</div>'
    )
