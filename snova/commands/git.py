# imports - standard imports
import os
import subprocess

# imports - module imports
from snova.snova import Snova
from snova.app import get_repo_dir
from snova.utils import set_git_remote_url
from snova.utils.app import get_remote

# imports - third party imports
import click


@click.command('remote-set-url', help="Set app remote url")
@click.argument('git-url')
def remote_set_url(git_url):
	set_git_remote_url(git_url)


@click.command('remote-reset-url', help="Reset app remote url to sparrow official")
@click.argument('app')
def remote_reset_url(app):
	git_url = f"https://github.com/sparrow/{app}.git"
	set_git_remote_url(git_url)


@click.command('remote-urls', help="Show apps remote url")
def remote_urls():
	for app in Snova(".").apps:
		repo_dir = get_repo_dir(app)

		if os.path.exists(os.path.join(repo_dir, '.git')):
			remote = get_remote(app)
			remote_url = subprocess.check_output(['git', 'config', '--get', f'remote.{remote}.url'], cwd=repo_dir).strip()
			print(f"{app}\t{remote_url}")

