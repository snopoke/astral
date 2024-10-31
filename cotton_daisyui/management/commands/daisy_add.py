import pathlib

from django.conf import settings
from django.core.management import BaseCommand, CommandError

APP_DIR = pathlib.Path(__file__).parent.parent.parent


class Command(BaseCommand):
    help = "Add a DaisyUI component to your project"

    def add_arguments(self, parser):
        parser.add_argument(
            "component", type=str, help="The name of the DaisyUI component to add"
        )
        parser.add_argument(
            "-n",
            "--namespace",
            type=str,
            help="The namespace to add the component with. "
            "If not provided, the component will be added to the root namespace.",
            default="",
        )
        parser.add_argument(
            "-t",
            "--template-path",
            type=str,
            help="The path to the template folder to use for the component",
        )

    def handle(
        self, component: str, namespace: str, template_path: str = None, **options
    ):
        component_path = _find_component(component)
        print(component_path)
        text = component_path.read_text().replace("daisyui.", namespace)

        if template_path:
            target_path = _get_target_path(component, namespace, template_path)
        else:
            dirs = list(_get_template_dirs())
            if dirs:
                template_path = dirs[0]
                if len(dirs) > 1:
                    print("Multiple template directories found. Please select one:")
                    for i, dir_name in enumerate(dirs):
                        print(f"{i}: {dir_name}")
                    choice = int(input("Enter the number of the directory to use: "))
                    template_path = dirs[choice]
                target_path = _get_target_path(component, namespace, template_path)
            else:
                raise CommandError("Please specify a template path with the -t option")

        target_path.write_text(text)


def _get_template_dirs():
    for template_settings in settings.TEMPLATES:
        if (
            template_settings["BACKEND"]
            == "django.template.backends.django.DjangoTemplates"
        ):
            yield from template_settings["DIRS"]


def _get_target_path(component, namespace, template_path):
    cotton_dir = getattr(settings, "COTTON_DIR", "cotton")
    target_path = pathlib.Path(template_path)
    if not template_path.rstrip("/").endswith(cotton_dir):
        target_path = target_path / cotton_dir
    if namespace:
        target_path = target_path / namespace
    target_path.mkdir(parents=True, exist_ok=True)
    return target_path / f"{component}.html"


def _find_component(component: str) -> pathlib.Path:
    path = APP_DIR / "templates" / "cotton" / "daisyui" / f"{component}.html"
    if not path.exists():
        raise CommandError(f"Component '{component}' not found")
    return path
