import pytest
import subprocess
import os
import shutil
import glob

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

    xml = os.path.join(destination,"environment.xml")
    try:
        subprocess.call(["./../mchgen/mchgen.sh",name,destination])
        subprocess.call(["./envgen.sh",xml,destination])

    except:
        subprocess.call(["./mchgen.sh",name,destination],cwd="./mchgen/")
        subprocess.call(["./envgen.sh",xml,destination],cwd="./envgen/")

    yield destination
    try:
        shutil.rmtree(destination)
    except FileNotFoundError:
        pass

def test_machine_skeleton_creation(machine_directory):
    created_env = os.path.join(machine_directory,"env")
    assert os.path.isdir(machine_directory)
    assert os.path.isdir(created_env)
    assert os.path.isfile(os.path.join(created_env,"environment.sh"))
    created_scripts = glob.glob(os.path.join(created_env,"*.bork"))
    assert len(created_scripts) > 0
