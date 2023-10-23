VERSION = "5.18.0"
PROJECT_NAME = "frappe-snova"
FRAPPE_VERSION = None
current_path = None
updated_path = None
LOG_BUFFER = []


def set_frappe_version(snova_path="."):
	from .utils.app import get_current_frappe_version

	global FRAPPE_VERSION
	if not FRAPPE_VERSION:
		FRAPPE_VERSION = get_current_frappe_version(snova_path=snova_path)
