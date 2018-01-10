import pytest
import subprocess
import os
import shutil

@pytest.fixture(scope='session')
def machine_directory():
    name = "test"
    destination = "/tmp/{}".format(name)
    # use try/except to allow pytest to be
    # called from inside mchgen dir or from
    # ma dir
    try:
        shutil.rmtree(destination)
    except FileNotFoundError:
        pass

    try:
        subprocess.call(["./mchgen.sh",name,destination])
    except:
        subprocess.call(["./mchgen.sh",name,destination],cwd="./mchgen/")

    yield destination
    shutil.rmtree(destination)

def test_machine_skeleton_creation(machine_directory):
    machine_files = [
        "environment.xml",
        "environment.sh",
        "helloworlds.py",
        "machine.xml",
        ".gitignore",
        "README.md",
        "LICENSE",
        "AUTHORS"
    ]
    assert os.path.isdir(machine_directory)
    assert sorted(machine_files) == sorted(os.listdir(machine_directory))
