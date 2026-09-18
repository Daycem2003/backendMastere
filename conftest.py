# `test_imports.py` is a manual dev smoke script (module-level prints + a single
# DB read), not a real pytest test. Excluding it from collection avoids
# pytest-django raising "Database access not allowed" at import time.
collect_ignore = ["test_imports.py"]
