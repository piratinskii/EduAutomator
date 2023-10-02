import subprocess
import pkg_resources

"""
This script is used to install the packages required for the program to operate and subsequently launch the main program. Use it only for the initial launch.
"""
required_packages = {
    d.name for d in pkg_resources.working_set
}

with open("requirements.txt", "r") as f:
    for line in f:
        package_name = line.strip().split("==")[0]
        if package_name not in required_packages:
            subprocess.check_call(["pip", "install", package_name])

subprocess.Popen(["python", "main.py"])
