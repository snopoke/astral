import pathlib
from typing import Generator, Set

from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django_cotton.compiler_regex import Tag

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
            help="The namespace to add the component to. "
            "If not provided, the component will be added to the root namespace.",
            default="",
        )
        parser.add_argument(
            "-t",
            "--template-path",
            type=str,
            help="The path to the template folder to use for the component",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite the component if it already exists",
        )
        parser.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            help="Don't ask for confirmation",
        )

    def handle(
        self,
        component: str,
        namespace: str,
        template_path: str,
        overwrite: bool,
        quiet: bool,
        **options,
    ):
        component_content = self._get_component_content(component)

        target_base_path = self._determine_target_path(namespace, template_path, quiet)

        dependencies = self._get_dependencies(component_content)
        if dependencies and not quiet:
            self._print_dependencies(dependencies)
            if not self._confirm("Continue?"):
                raise CommandError("Aborted")

        self._copy_components(
            namespace, component, dependencies, target_base_path, overwrite, quiet
        )

    def _determine_target_path(
        self, namespace: str, template_path: str, quiet: bool
    ) -> pathlib.Path:
        if template_path:
            return self._get_target_path(namespace, template_path)
        else:
            dirs = list(self._get_template_dirs())
            if not dirs:
                raise CommandError("Please specify a template path with the -t option")
            if len(dirs) > 1 and not quiet:
                template_path = self._select_template_dir(dirs)
            else:
                template_path = dirs[0]
            return self._get_target_path(namespace, template_path)

    def _select_template_dir(self, dirs: list[str]) -> str:
        self.stdout.write("Multiple template directories found. Please select one:")
        for i, dir_name in enumerate(dirs):
            self.stdout.write(f"{i}: {dir_name}")
        choice = int(input("Enter the number of the directory to use: "))
        return dirs[choice]

    def _print_dependencies(self, dependencies: Set[str]):
        self.stdout.write("This will also add the following dependencies:")
        for dependency in dependencies:
            self.stdout.write(f" - {dependency}")

    def _copy_components(
        self,
        namespace: str,
        component: str,
        dependencies: Set[str],
        target_base_path: pathlib.Path,
        overwrite: bool,
        quiet: bool,
    ):
        to_copy = {component} | dependencies
        for component in to_copy:
            target_path = target_base_path / f"{component}.html"
            if not overwrite and target_path.exists():
                exists_msg = f"Component '{component}' already exists at {target_path}"
                if quiet or not self._confirm(f"{exists_msg}. Overwrite? [y/N]"):
                    raise CommandError(exists_msg if quiet else "Aborted")

            self.stdout.write(f"Adding {component} to {target_path}...")
            target_path.write_text(self._get_component_content(component, namespace))

    def _get_template_dirs(self) -> Generator[str, None, None]:
        for template_settings in settings.TEMPLATES:
            if (
                template_settings["BACKEND"]
                == "django.template.backends.django.DjangoTemplates"
            ):
                yield from template_settings["DIRS"]

    def _get_target_path(self, namespace: str, template_path: str) -> pathlib.Path:
        cotton_dir = getattr(settings, "COTTON_DIR", "cotton")
        target_path = pathlib.Path(template_path)
        if not template_path.rstrip("/").endswith(cotton_dir):
            target_path = target_path / cotton_dir
        if namespace:
            target_path = target_path / namespace
        target_path.mkdir(parents=True, exist_ok=True)
        return target_path

    def _get_component_content(self, component: str, namespace: str = "daisyui") -> str:
        path = APP_DIR / "templates" / "cotton" / "daisyui" / f"{component}.html"
        if not path.exists():
            raise CommandError(f"Component '{component}' not found")
        content = path.read_text()
        namespace = f"{namespace.lstrip('.')}." if namespace else ""
        return content.replace("daisyui.", f"{namespace}")

    def _get_dependencies(self, component_content: str) -> Set[str]:
        prefix = "c-daisyui."
        dependencies = set()
        # what about `<c-component is="" />` dependencies?
        for match in Tag.tag_pattern.finditer(component_content):
            tag = Tag(match)
            if tag.tag_name.startswith(prefix):
                dependency = tag.tag_name.removeprefix(prefix).replace("-", "_")
                dependencies.add(dependency)
        return dependencies

    def _confirm(self, msg: str) -> bool:
        return input(f"{msg} [y/N] ").lower().startswith("y")
