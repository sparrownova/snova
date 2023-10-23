VERSION = "5.18.0"
PROJECT_NAME = "sparrow-bench"
Sparrow_VERSION = None
current_path = None
updated_path = None
LOG_BUFFER = []


def set_sparrow_version(bench_path="."):
	from .utils.app import get_current_sparrow_version

	globalSPARROW_VERSION
	if notSPARROW_VERSION:
		Sparrow_VERSION = get_current_sparrow_version(bench_path=bench_path)