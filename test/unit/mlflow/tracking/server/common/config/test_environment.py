import os
import unittest

from src.mlflow.tracking.server.common.config.environment import demand_env_var
from src.mlflow.tracking.server.common.config.environment_variable_not_found_error import (
    EnvironmentVariableNotFoundError,
)


class TestEnvironment(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["FAKE_VALUE"] = "mock-value"
        os.environ["INT_VALUE"] = "1"
        os.environ["FLOAT_VALUE"] = "3.14"

    def tearDown(self) -> None:
        if "FAKE_VALUE" in os.environ:
            del os.environ["FAKE_VALUE"]
        if "INT_VALUE" in os.environ:
            del os.environ["INT_VALUE"]
        if "FLOAT_VALUE" in os.environ:
            del os.environ["FLOAT_VALUE"]

    def test_demand_env_var(self):
        self.assertEqual(demand_env_var("FAKE_VALUE"), os.environ["FAKE_VALUE"])

    def test_demand_env_var_should_gracefully_fail(self):
        with self.assertRaises(EnvironmentVariableNotFoundError) as context:
            demand_env_var("SOME_VALUE")
        self.assertEqual(str(context.exception), "Environment variable (SOME_VALUE) not found")


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(TestEnvironment())
