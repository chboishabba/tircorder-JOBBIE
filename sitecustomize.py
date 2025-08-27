"""Test configuration that prevents auto-loading third-party pytest plugins."""

import os

# Prevent pytest from loading external plugins via entry points, which can
# interfere with our isolated test environment.
os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
