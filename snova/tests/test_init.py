# imports - standard imports
import json
import os
import subprocess
import unittest

# imports - third paty imports
import git

# imports - module imports
from snova.utils import exec_cmd
from snova.app import App
from snova.tests.test_base import FRAPPE_BRANCH, TestSnovaBase
from snova.snova import Snova


# changed from frappe_theme because it wasn't maintained and incompatible,
# chat app & wiki was breaking too. hopefully frappe_docs will be maintained
# for longer since docs.shopper.com is powered by it ;)
TEST_FRAPPE_APP = "frappe_docs"


class TestSnovaInit(TestSnovaBase):
	def test_utils(self):
		self.assertEqual(subprocess.call("snova"), 0)

	def test_init(self, snova_name="test-snova", **kwargs):
		self.init_snova(snova_name, **kwargs)
		app = App("file:///tmp/frappe")
		self.assertTupleEqual(
			(app.mount_path, app.url, app.repo, app.app_name, app.org),
			("/tmp/frappe", "file:///tmp/frappe", "frappe", "frappe", "frappe"),
		)
		self.assert_folders(snova_name)
		self.assert_virtual_env(snova_name)
		self.assert_config(snova_name)
		test_snova = Snova(snova_name)
		app = App("frappe", snova=test_snova)
		self.assertEqual(app.from_apps, True)

	def basic(self):
		try:
			self.test_init()
		except Exception:
			print(self.get_traceback())

	def test_multiple_snovaes(self):
		for snova_name in ("test-snova-1", "test-snova-2"):
			self.init_snova(snova_name, skip_assets=True)

		self.assert_common_site_config(
			"test-snova-1",
			{
				"webserver_port": 8000,
				"socketio_port": 9000,
				"file_watcher_port": 6787,
				"redis_queue": "redis://127.0.0.1:11000",
				"redis_socketio": "redis://127.0.0.1:13000",
				"redis_cache": "redis://127.0.0.1:13000",
			},
		)

		self.assert_common_site_config(
			"test-snova-2",
			{
				"webserver_port": 8001,
				"socketio_port": 9001,
				"file_watcher_port": 6788,
				"redis_queue": "redis://127.0.0.1:11001",
				"redis_socketio": "redis://127.0.0.1:13001",
				"redis_cache": "redis://127.0.0.1:13001",
			},
		)

	def test_new_site(self):
		snova_name = "test-snova"
		site_name = "test-site.local"
		snova_path = os.path.join(self.snovaes_path, snova_name)
		site_path = os.path.join(snova_path, "sites", site_name)
		site_config_path = os.path.join(site_path, "site_config.json")

		self.init_snova(snova_name)
		self.new_site(site_name, snova_name)

		self.assertTrue(os.path.exists(site_path))
		self.assertTrue(os.path.exists(os.path.join(site_path, "private", "backups")))
		self.assertTrue(os.path.exists(os.path.join(site_path, "private", "files")))
		self.assertTrue(os.path.exists(os.path.join(site_path, "public", "files")))
		self.assertTrue(os.path.exists(site_config_path))

		with open(site_config_path) as f:
			site_config = json.loads(f.read())

			for key in ("db_name", "db_password"):
				self.assertTrue(key in site_config)
				self.assertTrue(site_config[key])

	def test_get_app(self):
		self.init_snova("test-snova", skip_assets=True)
		snova_path = os.path.join(self.snovaes_path, "test-snova")
		exec_cmd(f"snova get-app {TEST_FRAPPE_APP} --skip-assets", cwd=snova_path)
		self.assertTrue(os.path.exists(os.path.join(snova_path, "apps", TEST_FRAPPE_APP)))
		app_installed_in_env = TEST_FRAPPE_APP in subprocess.check_output(
			["snova", "pip", "freeze"], cwd=snova_path
		).decode("utf8")
		self.assertTrue(app_installed_in_env)

	@unittest.skipIf(FRAPPE_BRANCH != "develop", "only for develop branch")
	def test_get_app_resolve_deps(self):
		FRAPPE_APP = "healthcare"
		self.init_snova("test-snova", skip_assets=True)
		snova_path = os.path.join(self.snovaes_path, "test-snova")
		exec_cmd(f"snova get-app {FRAPPE_APP} --resolve-deps --skip-assets", cwd=snova_path)
		self.assertTrue(os.path.exists(os.path.join(snova_path, "apps", FRAPPE_APP)))

		states_path = os.path.join(snova_path, "sites", "apps.json")
		self.assertTrue(os.path.exists(states_path))

		with open(states_path) as f:
			states = json.load(f)

		self.assertTrue(FRAPPE_APP in states)

	def test_install_app(self):
		snova_name = "test-snova"
		site_name = "install-app.test"
		snova_path = os.path.join(self.snovaes_path, "test-snova")

		self.init_snova(snova_name, skip_assets=True)
		exec_cmd(
			f"snova get-app {TEST_FRAPPE_APP} --branch master --skip-assets", cwd=snova_path
		)

		self.assertTrue(os.path.exists(os.path.join(snova_path, "apps", TEST_FRAPPE_APP)))

		# check if app is installed
		app_installed_in_env = TEST_FRAPPE_APP in subprocess.check_output(
			["snova", "pip", "freeze"], cwd=snova_path
		).decode("utf8")
		self.assertTrue(app_installed_in_env)

		# create and install app on site
		self.new_site(site_name, snova_name)
		installed_app = not exec_cmd(
			f"snova --site {site_name} install-app {TEST_FRAPPE_APP}",
			cwd=snova_path,
			_raise=False,
		)

		if installed_app:
			app_installed_on_site = subprocess.check_output(
				["snova", "--site", site_name, "list-apps"], cwd=snova_path
			).decode("utf8")
			self.assertTrue(TEST_FRAPPE_APP in app_installed_on_site)

	def test_remove_app(self):
		self.init_snova("test-snova", skip_assets=True)
		snova_path = os.path.join(self.snovaes_path, "test-snova")

		exec_cmd(
			f"snova get-app {TEST_FRAPPE_APP} --branch master --overwrite --skip-assets",
			cwd=snova_path,
		)
		exec_cmd(f"snova remove-app {TEST_FRAPPE_APP}", cwd=snova_path)

		with open(os.path.join(snova_path, "sites", "apps.txt")) as f:
			self.assertFalse(TEST_FRAPPE_APP in f.read())
		self.assertFalse(
			TEST_FRAPPE_APP
			in subprocess.check_output(["snova", "pip", "freeze"], cwd=snova_path).decode("utf8")
		)
		self.assertFalse(os.path.exists(os.path.join(snova_path, "apps", TEST_FRAPPE_APP)))

	def test_switch_to_branch(self):
		self.init_snova("test-snova", skip_assets=True)
		snova_path = os.path.join(self.snovaes_path, "test-snova")
		app_path = os.path.join(snova_path, "apps", "frappe")

		# * chore: change to 14 when avalible
		prevoius_branch = "version-13"
		if FRAPPE_BRANCH != "develop":
			# assuming we follow `version-#`
			prevoius_branch = f"version-{int(FRAPPE_BRANCH.split('-')[1]) - 1}"

		successful_switch = not exec_cmd(
			f"snova switch-to-branch {prevoius_branch} frappe --upgrade",
			cwd=snova_path,
			_raise=False,
		)
		if successful_switch:
			app_branch_after_switch = str(git.Repo(path=app_path).active_branch)
			self.assertEqual(prevoius_branch, app_branch_after_switch)

		successful_switch = not exec_cmd(
			f"snova switch-to-branch {FRAPPE_BRANCH} frappe --upgrade",
			cwd=snova_path,
			_raise=False,
		)
		if successful_switch:
			app_branch_after_second_switch = str(git.Repo(path=app_path).active_branch)
			self.assertEqual(FRAPPE_BRANCH, app_branch_after_second_switch)


if __name__ == "__main__":
	unittest.main()
