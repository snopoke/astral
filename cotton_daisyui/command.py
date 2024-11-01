import argparse
import os
import pathlib
import sys
from typing import Generator, Set

from django.conf import settings
from django.core.management import color_style
from django.core.management.base import OutputWrapper
from django_cotton.compiler_regex import Tag

APP_DIR = pathlib.Path(__file__).parent

stdout = OutputWrapper(sys.stdout)
stderr = OutputWrapper(sys.stderr)
style = color_style()
stderr.style_func = style.ERROR


class DaisyAddCommandError(Exception):
    pass


def main():
    options = _get_options()
    _configure_django_settings(options)
    target_base_path = _determine_target_path(
        options.namespace, options.template_path, options.quiet, options.pythonpath
    )
    import_component(
        options.component,
        options.namespace,
        target_base_path,
        options.overwrite,
        options.quiet,
    )


def import_component(
    component: str,
    namespace: str,
    template_path: pathlib.Path,
    overwrite: bool,
    quiet: bool,
):
    component_content = _get_component_content(component)

    dependencies = _get_dependencies(component_content)
    if dependencies and not quiet:
        _print_dependencies(dependencies)
        if not _confirm("Continue?"):
            raise DaisyAddCommandError("Aborted")

    _copy_components(
        namespace, component, dependencies, template_path, overwrite, quiet
    )


def _determine_target_path(
    namespace: str, template_path: str, quiet: bool, pythonpath: str = None
) -> pathlib.Path:
    if template_path:
        return _get_target_path(namespace, template_path)
    else:
        dirs = list(_get_template_dirs())
        if not dirs:
            raise DaisyAddCommandError(
                "Please specify a template path with the -t option"
            )
        if len(dirs) > 1 and not quiet:
            template_path = _select_template_dir(dirs)
        else:
            template_path = dirs[0]

        if not pathlib.Path(template_path).exists():
            if pythonpath:
                template_path = pathlib.Path(pythonpath) / template_path
            if not template_path.exists():
                raise DaisyAddCommandError(f"Template path not found: {template_path}")

        return _get_target_path(namespace, str(template_path))


def _select_template_dir(dirs: list[str]) -> str:
    stdout.write("Multiple template directories found. Please select one:")
    for i, dir_name in enumerate(dirs):
        stdout.write(f"{i}: {dir_name}")
    choice = int(input("Enter the number of the directory to use: "))
    return dirs[choice]


def _print_dependencies(dependencies: Set[str]):
    stdout.write("This will also add the following dependencies:")
    for dependency in dependencies:
        stdout.write(f" - {dependency}")


def _copy_components(
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
            if quiet or not _confirm(f"{exists_msg}. Overwrite? [y/N]"):
                raise DaisyAddCommandError(exists_msg if quiet else "Aborted")

        stdout.write(f"Adding {component} to {target_path}...")
        target_path.write_text(_get_component_content(component, namespace))


def _get_template_dirs() -> Generator[str, None, None]:
    for template_settings in settings.TEMPLATES:
        if (
            template_settings["BACKEND"]
            == "django.template.backends.django.DjangoTemplates"
        ):
            yield from template_settings["DIRS"]


def _get_target_path(namespace: str, template_path: str) -> pathlib.Path:
    cotton_dir = getattr(settings, "COTTON_DIR", "cotton")
    target_path = pathlib.Path(template_path)
    if not template_path.rstrip("/").endswith(cotton_dir):
        target_path = target_path / cotton_dir
    if namespace:
        target_path = target_path / namespace
    target_path.mkdir(parents=True, exist_ok=True)
    return target_path


def _get_component_content(component: str, namespace: str = "daisyui") -> str:
    path = APP_DIR / "templates" / "cotton" / "daisyui" / f"{component}.html"
    if not path.exists():
        raise DaisyAddCommandError(f"Component '{component}' not found")
    content = path.read_text()
    namespace = f"{namespace.lstrip('.')}." if namespace else ""
    return content.replace("daisyui.", f"{namespace}")


def _get_dependencies(component_content: str) -> Set[str]:
    prefix = "c-daisyui."
    dependencies = set()
    # what about `<c-component is="" />` dependencies?
    for match in Tag.tag_pattern.finditer(component_content):
        tag = Tag(match)
        if tag.tag_name.startswith(prefix):
            dependency = tag.tag_name.removeprefix(prefix).replace("-", "_")
            dependencies.add(dependency)
    return dependencies


def _confirm(msg: str) -> bool:
    return input(f"{msg} [y/N] ").lower().startswith("y")


def _configure_django_settings(options):
    if options.settings:
        os.environ["DJANGO_SETTINGS_MODULE"] = options.settings
    elif not os.getenv("DJANGO_SETTINGS_MODULE"):
        stderr.write("DJANGO_SETTINGS_MODULE not set")
        sys.exit(1)

    if options.pythonpath:
        if not pathlib.Path(options.pythonpath).exists():
            stderr.write(f"Python path not found: {options.pythonpath}")
            sys.exit(1)
        sys.path.insert(0, options.pythonpath)

    try:
        settings.INSTALLED_APPS
    except ModuleNotFoundError as e:
        stderr.write(f"Could not import settings: {e}\nTry setting the pythonpath")
        sys.exit(1)
    if not settings.configured:
        stderr.write("Django settings not configured")


def _get_options():
    parser = argparse.ArgumentParser(description="Cotton Daisy CLI")
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
    parser.add_argument(
        "--settings",
        default=os.getenv("DJANGO_SETTINGS_MODULE"),
        help="The Django settings module to use",
    )
    parser.add_argument(
        "--pythonpath",
        default=os.getenv("PYTHONPATH"),
        help="The Python path to use",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
