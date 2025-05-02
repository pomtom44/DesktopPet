#!/usr/bin/env python3
"""
Installation script for DesktopPet requirements.
This script installs all the necessary Python packages listed in requirements.txt.
"""

import subprocess
import sys


def install_requirements():
    """Install all requirements from requirements.txt using pip."""
    try:
        # Use the current Python interpreter to run pip
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            "requirements.txt"
        ])
        print("\n✅ All requirements have been successfully installed!")
    except subprocess.CalledProcessError as error:
        print(f"\n❌ Error occurred while installing requirements: {error}")
        sys.exit(1)


if __name__ == "__main__":
    print("📦 Installing required packages...")
    install_requirements() 