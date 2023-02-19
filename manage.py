#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import dotenv

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    dotenv.read_dotenv()
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
# ID=YXAvwIXHvX2IU7lsMxfWyznRFUpg8ExRlvSAg6k4
# SECRET=pbkdf2_sha256$390000$UK0DxSvA6dD9RWtuG2Qnq6$eTw7lPYeJP9YOfTdsXy0AVK9GMUwCswpP7mDWaUEVGw=