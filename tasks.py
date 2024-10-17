from invoke.tasks import task


@task
def build_tailwind(ctx, watch=False):
    cmd = "npx tailwindcss -i ./example-project/static/input.css -o example-project/static/output.css"
    if watch:
        cmd += " --watch"
    ctx.run(cmd, pty=True)


@task
def run_example(ctx):
    with ctx.cd("example-project"):
        ctx.run("python manage.py runserver", pty=True)
