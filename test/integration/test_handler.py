import os
import shlex
import subprocess
import time
import unittest
from typing import Optional

import psutil
import requests
import yaml
from requests import Response


def load_commands() -> dict:
    with open(file="anaconda-project.yml", mode="r", encoding="utf-8") as file:
        project: dict = yaml.safe_load(file)
    return project


class TestHandler(unittest.TestCase):
    process: Optional[subprocess.Popen]

    def setUp(self) -> None:
        os.environ["MLFLOW_BACKEND_STORE_URI"] = "sqlite:///test/fixtures/mlflow/local/store/mydb.sqlite"
        os.environ["MLFLOW_ARTIFACTS_DESTINATION"] = "test/fixtures/mlflow/local/artifacts"
        self.project = load_commands()

    def test_launch_server(self):
        shell_out_cmd: str = self.project["commands"]["TrackingServer"]["unix"]
        args = shlex.split(shell_out_cmd)

        try:
            self.process = subprocess.Popen(args, stdout=subprocess.PIPE)
        except Exception as error:
            # Any failure here is a failed test.
            self.fail(f"Failed to start server process: {str(error)}")

        max_tries: int = 10
        max_wait: int = 5

        current_try: int = 1
        while current_try <= max_tries:
            current_try += 1

            try:
                response: Response = requests.get(url="http://0.0.0.0:8086")

                if response.status_code != 200:
                    print("waiting ...")
                    time.sleep(max_wait)
                else:
                    print("server online")
                    break

            except requests.exceptions.ConnectionError:
                print("waiting ...")
                time.sleep(max_wait)

        print("shutting down test")
        try:
            if self.process is not None:
                parent = psutil.Process(self.process.pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
        except Exception as error:
            # Any failure here is a failed test.
            self.fail(f"Failed to stop server process: {str(error)}")

        self.assertLessEqual(current_try, max_tries)

    def test_launch_gc(self):
        shell_out_cmd: str = self.project["commands"]["GarbageCollection"]["unix"]
        args = shlex.split(shell_out_cmd)

        try:
            self.process = subprocess.Popen(args, stdout=subprocess.PIPE)
        except Exception as error:
            # Any failure here is a failed test.
            self.fail(f"Failed to start server gc process: {str(error)}")

        max_tries: int = 10
        max_wait: int = 5

        current_try: int = 1
        while current_try <= max_tries:
            print(f"checking, {current_try} of {max_tries}")
            current_try += 1
            self.process.poll()
            if self.process.returncode != 0:
                print("waiting ...")
                time.sleep(max_wait)
            else:
                break
        try:
            if self.process is not None and self.process.returncode is None:
                print("manually terminating process")
                parent = psutil.Process(self.process.pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
                self.fail(f"Failed to complete gc in time frame")
        except Exception as error:
            # Any failure here is a failed test.
            self.fail(f"Failed to stop process: {str(error)}")

        self.assertLessEqual(current_try, max_tries)

    def test_launch_db_upgrade(self):
        shell_out_cmd: str = self.project["commands"]["DatabaseUpgrade"]["unix"]
        args = shlex.split(shell_out_cmd)

        try:
            self.process = subprocess.Popen(args, stdout=subprocess.PIPE)
        except Exception as error:
            # Any failure here is a failed test.
            self.fail(f"Failed to start server db upgrade process: {str(error)}")

        max_tries: int = 10
        max_wait: int = 5

        current_try: int = 1
        while current_try <= max_tries:
            print(f"checking, {current_try} of {max_tries}")
            current_try += 1
            self.process.poll()
            if self.process.returncode != 0:
                print("waiting ...")
                time.sleep(max_wait)
            else:
                break
        try:
            if self.process is not None and self.process.returncode is None:
                print("manually terminating process")
                parent = psutil.Process(self.process.pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
                self.fail(f"Failed to complete db upgrade in time frame")
        except Exception as error:
            # Any failure here is a failed test.
            self.fail(f"Failed to stop process: {str(error)}")

        self.assertLessEqual(current_try, max_tries)


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(TestHandler())
