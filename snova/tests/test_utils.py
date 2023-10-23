import os
import shutil
import subprocess
import unittest

from snova.app import App
from snova.snova import Snova
from snova.exceptions import InvalidRemoteException
from snova.utils import is_valid_frappe_branch


class TestUtils(unittest.TestCase):
	def test_app_utils(self):
		git_url = "https://github.com/sparrownova/sparrow"
		branch = "develop"
		app = App(name=git_url, branch=branch, snova=Snova("."))
		self.assertTrue(
			all(
				[
					app.name == git_url,
					app.branch == branch,
					app.tag == branch,
					app.is_url is True,
					app.on_disk is False,
					app.org == "frappe",
					app.url == git_url,
				]
			)
		)

	def test_is_valid_frappe_branch(self):
		with self.assertRaises(InvalidRemoteException):
			is_valid_frappe_branch(
				"https://github.com/sparrownova/sparrow.git", frappe_branch="random-branch"
			)
			is_valid_frappe_branch(
				"https://github.com/random/random.git", frappe_branch="random-branch"
			)

		is_valid_frappe_branch(
			"https://github.com/sparrownova/sparrow.git", frappe_branch="develop"
		)
		is_valid_frappe_branch(
			"https://github.com/sparrownova/sparrow.git", frappe_branch="v13.29.0"
		)

	def test_app_states(self):
		snova_dir = "./sandbox"
		sites_dir = os.path.join(snova_dir, "sites")

		if not os.path.exists(sites_dir):
			os.makedirs(sites_dir)

		fake_snova = Snova(snova_dir)

		self.assertTrue(hasattr(fake_snova.apps, "states"))

		fake_snova.apps.states = {
			"frappe": {
				"resolution": {"branch": "develop", "commit_hash": "234rwefd"},
				"version": "14.0.0-dev",
			}
		}
		fake_snova.apps.update_apps_states()

		self.assertEqual(fake_snova.apps.states, {})

		frappe_path = os.path.join(snova_dir, "apps", "frappe")

		os.makedirs(os.path.join(frappe_path, "frappe"))

		subprocess.run(["git", "init"], cwd=frappe_path, capture_output=True, check=True)

		with open(os.path.join(frappe_path, "frappe", "__init__.py"), "w+") as f:
			f.write("__version__ = '11.0'")

		subprocess.run(["git", "add", "."], cwd=frappe_path, capture_output=True, check=True)
		subprocess.run(
			["git", "config", "user.email", "snova-test_app_states@gha.com"],
			cwd=frappe_path,
			capture_output=True,
			check=True,
		)
		subprocess.run(
			["git", "config", "user.name", "App States Test"],
			cwd=frappe_path,
			capture_output=True,
			check=True,
		)
		subprocess.run(
			["git", "commit", "-m", "temp"], cwd=frappe_path, capture_output=True, check=True
		)

		fake_snova.apps.update_apps_states(app_name="frappe")

		self.assertIn("frappe", fake_snova.apps.states)
		self.assertIn("version", fake_snova.apps.states["frappe"])
		self.assertEqual("11.0", fake_snova.apps.states["frappe"]["version"])

		shutil.rmtree(snova_dir)

	def test_ssh_ports(self):
		app = App("git@github.com:22:frappe/frappe")
		self.assertEqual(
			(app.use_ssh, app.org, app.repo, app.app_name), (True, "frappe", "frappe", "frappe")
		)
