# imports - third party imports
import click


@click.command("init", help="Initialize a new snova instance in the specified path")
@click.argument("path")
@click.option(
	"--version",
	"--sparrow-branch",
	"sparrow_branch",
	default=None,
	help="Clone a particular branch of sparrow",
)
@click.option(
	"--ignore-exist", is_flag=True, default=False, help="Ignore if Snova instance exists."
)
@click.option(
	"--python", type=str, default="python3", help="Path to Python Executable."
)
@click.option(
	"--apps_path", default=None, help="path to json files with apps to install after init"
)
@click.option("--sparrow-path", default=None, help="path to sparrow repo")
@click.option("--clone-from", default=None, help="copy repos from path")
@click.option(
	"--clone-without-update", is_flag=True, help="copy repos from path without update"
)
@click.option("--no-procfile", is_flag=True, help="Do not create a Procfile")
@click.option(
	"--no-backups",
	is_flag=True,
	help="Do not set up automatic periodic backups for all sites on this snova",
)
@click.option(
	"--skip-redis-config-generation",
	is_flag=True,
	help="Skip redis config generation if already specifying the common-site-config file",
)
@click.option("--skip-assets", is_flag=True, default=False, help="Do not build assets")
@click.option("--install-app", help="Install particular app after initialization")
@click.option("--verbose", is_flag=True, help="Verbose output during install")
def init(
	path,
	apps_path,
	sparrow_path,
	sparrow_branch,
	no_procfile,
	no_backups,
	clone_from,
	verbose,
	skip_redis_config_generation,
	clone_without_update,
	ignore_exist=False,
	skip_assets=False,
	python="python3",
	install_app=None,
):
	import os

	from snova.utils import log
	from snova.utils.system import init

	if not ignore_exist and os.path.exists(path):
		log(f"Snova instance already exists at {path}", level=2)
		return

	try:
		init(
			path,
			apps_path=apps_path,  # can be used from --config flag? Maybe config file could have more info?
			no_procfile=no_procfile,
			no_backups=no_backups,
			sparrow_path=sparrow_path,
			sparrow_branch=sparrow_branch,
			install_app=install_app,
			clone_from=clone_from,
			skip_redis_config_generation=skip_redis_config_generation,
			clone_without_update=clone_without_update,
			skip_assets=skip_assets,
			python=python,
			verbose=verbose,
		)
		log(f"Snova {path} initialized", level=1)
	except SystemExit:
		raise
	except Exception:
		import shutil
		import time

		from snova.utils import get_traceback

		# add a sleep here so that the traceback of other processes doesnt overlap with the prompts
		time.sleep(1)
		print(get_traceback())

		log(f"There was a problem while creating {path}", level=2)
		if click.confirm("Do you want to rollback these changes?", abort=True):
			log(f'Rolling back Snova "{path}"')
			if os.path.exists(path):
				shutil.rmtree(path)


@click.command("drop")
@click.argument("path")
def drop(path):
	from snova.snova import Snova
	from snova.exceptions import SnovaNotFoundError, ValidationError

	snova = Snova(path)

	if not snova.exists:
		raise SnovaNotFoundError(f"Snova {snova.name} does not exist")

	if snova.sites:
		raise ValidationError("Cannot remove non-empty snova directory")

	snova.drop()

	print("Snova dropped")


@click.command(
	["get", "get-app"],
	help="Clone an app from the internet or filesystem and set it up in your snova",
)
@click.argument("name", nargs=-1)  # Dummy argument for backward compatibility
@click.argument("git-url")
@click.option("--branch", default=None, help="branch to checkout")
@click.option("--overwrite", is_flag=True, default=False)
@click.option("--skip-assets", is_flag=True, default=False, help="Do not build assets")
@click.option(
	"--soft-link",
	is_flag=True,
	default=False,
	help="Create a soft link to git repo instead of clone.",
)
@click.option(
	"--init-snova", is_flag=True, default=False, help="Initialize Snova if not in one"
)
@click.option(
	"--resolve-deps",
	is_flag=True,
	default=False,
	help="Resolve dependencies before installing app",
)
def get_app(
	git_url,
	branch,
	name=None,
	overwrite=False,
	skip_assets=False,
	soft_link=False,
	init_snova=False,
	resolve_deps=False,
):
	"clone an app from the internet and set it up in your snova"
	from snova.app import get_app

	get_app(
		git_url,
		branch=branch,
		skip_assets=skip_assets,
		overwrite=overwrite,
		soft_link=soft_link,
		init_snova=init_snova,
		resolve_deps=resolve_deps,
	)


@click.command("new-app", help="Create a new Sparrow application under apps folder")
@click.option(
	"--no-git",
	is_flag=True,
	flag_value="--no-git",
	help="Do not initialize git repository for the app (available in Sparrow v14+)",
)
@click.argument("app-name")
def new_app(app_name, no_git=None):
	from snova.app import new_app

	new_app(app_name, no_git)


@click.command(
	["remove", "rm", "remove-app"],
	help=(
		"Completely remove app from snova and re-build assets if not installed on any site"
	),
)
@click.option("--no-backup", is_flag=True, help="Do not backup app before removing")
@click.option("--force", is_flag=True, help="Force remove app")
@click.argument("app-name")
def remove_app(app_name, no_backup=False, force=False):
	from snova.snova import Snova

	snova = Snova(".")
	snova.uninstall(app_name, no_backup=no_backup, force=force)


@click.command("exclude-app", help="Exclude app from updating")
@click.argument("app_name")
def exclude_app_for_update(app_name):
	from snova.app import add_to_excluded_apps_txt

	add_to_excluded_apps_txt(app_name)


@click.command("include-app", help="Include app for updating")
@click.argument("app_name")
def include_app_for_update(app_name):
	"Include app from updating"
	from snova.app import remove_from_excluded_apps_txt

	remove_from_excluded_apps_txt(app_name)


@click.command(
	"pip",
	context_settings={"ignore_unknown_options": True, "help_option_names": []},
	help="For pip help use `snova pip help [COMMAND]` or `snova pip [COMMAND] -h`",
)
@click.argument("args", nargs=-1)
@click.pass_context
def pip(ctx, args):
	"Run pip commands in snova env"
	import os

	from snova.utils.snova import get_env_cmd

	env_py = get_env_cmd("python")
	os.execv(env_py, (env_py, "-m", "pip") + args)