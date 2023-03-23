import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.mlflow.tracking.server.common.config.environment import demand_env_var
from src.mlflow.tracking.server.contracts.dto.launch_parameters import LaunchParameters
from src.mlflow.tracking.server.contracts.types.activity import ActivityType
from src.mlflow.tracking.server.controller import MLFlowTrackingServerController


class TestController(unittest.TestCase):
    # _ensure_sane_runtime_environment tests

    def test_ensure_sane_runtime_environment_needs_to_create_structures(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store_uri: str = f"sqlite:///{tmp_dir}/mlflow/local/store/mydb.sqlite"
            artifacts_destination: str = f"{tmp_dir}/mlflow/local/artifacts"
            os.environ["MLFLOW_BACKEND_STORE_URI"] = store_uri
            os.environ["MLFLOW_ARTIFACTS_DESTINATION"] = artifacts_destination

            with patch("pathlib.Path.__new__") as patched_path:
                patched_path.reset_mock()
                parent = MagicMock()
                patched_path.parent = parent
                MLFlowTrackingServerController._ensure_sane_runtime_environment()

                # Ensure if sqllite is selected that the file system location exists
                self.assertEqual(patched_path.call_count, 2)
                self.assertEqual(patched_path.mock_calls[0].args[1], f"{tmp_dir}/mlflow/local/store/mydb.sqlite")
                self.assertEqual(patched_path.mock_calls[4].args[1], artifacts_destination)

    def test_ensure_sane_runtime_environment_was_not_given_sqllite(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store_uri: str = f"unsupported:///{tmp_dir}/mlflow/local/store/mydb.sqlite"
            artifacts_destination: str = f"{tmp_dir}/mlflow/local/artifacts"
            os.environ["MLFLOW_BACKEND_STORE_URI"] = store_uri
            os.environ["MLFLOW_ARTIFACTS_DESTINATION"] = artifacts_destination

            with patch("pathlib.Path.__new__") as patched_path:
                patched_path.reset_mock()
                parent = MagicMock()
                patched_path.parent = parent
                MLFlowTrackingServerController._ensure_sane_runtime_environment()

                self.assertEqual(patched_path.call_count, 1)
                self.assertEqual(patched_path.mock_calls[0].args[1], artifacts_destination)

    # _process_launch tests

    def test_process_launch(self):
        with patch("subprocess.Popen.__new__") as patched_subprocess:
            patched_subprocess.reset_mock()

            class MockStdout:
                def readline(self):
                    return b""

            class MockProcess:
                stdout: MockStdout = MockStdout()

            patched_subprocess.return_value = MockProcess()

            MLFlowTrackingServerController()._process_launch(shell_out_cmd="mock command")

            self.assertEqual(patched_subprocess.call_count, 1)
            self.assertEqual(patched_subprocess.mock_calls[0].args[1], ["mock", "command"])

    # _process_launch_wait tests

    def test_process_launch_wait(self):
        with patch("subprocess.Popen.__new__") as patched_subprocess:
            patched_subprocess.reset_mock()

            class MockProcess:
                __enter__: MagicMock = MagicMock(side_effect=[Exception("MOCK")])
                __exit__: MagicMock = MagicMock()
                stdout: MagicMock = MagicMock()

            patched_subprocess.return_value = MockProcess()

            with self.assertRaises(Exception) as error:
                MLFlowTrackingServerController()._process_launch_wait(shell_out_cmd="mock command")
                self.assertEqual(error.exception, "MOCK")

            self.assertEqual(patched_subprocess.call_count, 1)
            self.assertEqual(patched_subprocess.mock_calls[0].args[1], ["mock", "command"])

    # execute tests

    # Server startup tests

    def test_execute_with_defaults(self):
        with patch(
            "src.mlflow.tracking.server.controller.MLFlowTrackingServerController._process_launch"
        ) as patched_launch:
            patched_launch.reset_mock()
            MLFlowTrackingServerController().execute(params=LaunchParameters(activity=ActivityType.SERVER))

            self.assertEqual(patched_launch.call_count, 1)
            self.assertEqual(
                patched_launch.call_args[1],
                {"shell_out_cmd": "mlflow server --serve-artifacts --port 8086 --host 0.0.0.0"},
            )

    def test_execute_with_customization(self):
        with patch(
            "src.mlflow.tracking.server.controller.MLFlowTrackingServerController._process_launch"
        ) as patched_launch:
            patched_launch.reset_mock()
            MLFlowTrackingServerController().execute(
                params=LaunchParameters(**{"sanity": True, "port": 0, "address": "localhost", "activity": "server"})
            )

            self.assertEqual(patched_launch.call_count, 1)
            self.assertEqual(
                patched_launch.call_args[1],
                {"shell_out_cmd": "mlflow server --serve-artifacts --port 0 --host localhost"},
            )

    def test_execute_with_gc(self):
        with patch(
            "src.mlflow.tracking.server.controller.MLFlowTrackingServerController._process_launch_wait"
        ) as patched_launch:
            patched_launch.reset_mock()
            MLFlowTrackingServerController().execute(params=LaunchParameters(activity=ActivityType.GC))

            self.assertEqual(patched_launch.call_count, 1)
            expected_launch_cmd: str = (
                "mlflow gc "
                f"--older-than {demand_env_var(name='MLFLOW_TRACKING_GC_TTL')} "
                f"--backend-store-uri {demand_env_var(name='MLFLOW_BACKEND_STORE_URI')}"
            )
            self.assertEqual(
                patched_launch.call_args[1],
                {"shell_out_cmd": expected_launch_cmd},
            )

    def test_execute_with_db_upgrade(self):
        with patch(
            "src.mlflow.tracking.server.controller.MLFlowTrackingServerController._process_launch_wait"
        ) as patched_launch:
            patched_launch.reset_mock()
            MLFlowTrackingServerController().execute(params=LaunchParameters(activity=ActivityType.DB_UPGRADE))

            self.assertEqual(patched_launch.call_count, 1)
            self.assertEqual(
                patched_launch.call_args[1],
                {"shell_out_cmd": f"mlflow db upgrade {demand_env_var(name='MLFLOW_BACKEND_STORE_URI')}"},
            )

    # perform_database_upgrade tests

    def test_perform_database_upgrade_dry_run(self):
        with patch(
            "src.mlflow.tracking.server.controller.MLFlowTrackingServerController._process_launch_wait"
        ) as patched_launch:
            patched_launch.reset_mock()
            MLFlowTrackingServerController().perform_database_upgrade()
            self.assertEqual(patched_launch.call_count, 0)

    def test_perform_database_upgrade(self):
        with patch(
            "src.mlflow.tracking.server.controller.MLFlowTrackingServerController._process_launch_wait"
        ) as patched_launch:
            patched_launch.reset_mock()
            MLFlowTrackingServerController().perform_database_upgrade(dry_run=False)

            self.assertEqual(patched_launch.call_count, 1)
            self.assertEqual(
                patched_launch.call_args[1],
                {"shell_out_cmd": f"mlflow db upgrade {demand_env_var(name='MLFLOW_BACKEND_STORE_URI')}"},
            )

    # garbage collection tests

    def test_perform_garbage_collection_dry_run(self):
        with patch(
            "src.mlflow.tracking.server.controller.MLFlowTrackingServerController._process_launch_wait"
        ) as patched_launch:
            patched_launch.reset_mock()
            MLFlowTrackingServerController().perform_garbage_collection()
            self.assertEqual(patched_launch.call_count, 0)

    def test_perform_garbage_collection(self):
        with patch(
            "src.mlflow.tracking.server.controller.MLFlowTrackingServerController._process_launch_wait"
        ) as patched_launch:
            patched_launch.reset_mock()
            MLFlowTrackingServerController().perform_garbage_collection(dry_run=False)
            self.assertEqual(patched_launch.call_count, 1)

            expected_launch_cmd: str = (
                "mlflow gc "
                f"--older-than {demand_env_var(name='MLFLOW_TRACKING_GC_TTL')} "
                f"--backend-store-uri {demand_env_var(name='MLFLOW_BACKEND_STORE_URI')}"
            )
            self.assertEqual(
                patched_launch.call_args[1],
                {"shell_out_cmd": expected_launch_cmd},
            )

    def test_should_fail_activity_type_check_with_grace(self):
        mock_params = LaunchParameters(activity=ActivityType.SERVER)
        mock_params.activity = "MOCK"
        with self.assertRaises(ValueError) as context:
            MLFlowTrackingServerController().execute(params=mock_params)
        self.assertEqual(str(context.exception), f"launch type {mock_params.activity} is not supported")


if __name__ == "__main__":
    runner = unittest.runner.TextTestRunner()
    runner.run(TestController())
