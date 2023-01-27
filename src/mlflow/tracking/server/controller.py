""" MLFlow Tracking Server Launch Controller """
import shlex
import subprocess
from pathlib import Path

from anaconda.enterprise.server.common.sdk import demand_env_var
from anaconda.enterprise.server.contracts import BaseModel

from .contracts.dto.launch_parameters import LaunchParameters
from .contracts.types.activity import ActivityType


# pylint: disable=fixme,too-few-public-methods
class MLFlowTrackingServerController(BaseModel):
    """
    Responsible for the invocation of the mlflow process.
    """

    @staticmethod
    def _ensure_sane_runtime_environment() -> None:
        """
        Creates the needed file system directory structure on the host required by MLFlow.
        This is required because MLFlow assumes this already exist and will fail to start
        if they are not present.
        """

        backend_uri: str = demand_env_var(name="MLFLOW_BACKEND_STORE_URI")
        if backend_uri.startswith("sqlite:///"):
            path: str = backend_uri.split(sep="sqlite:///")[1]
            parent: Path = Path(path).parent.resolve()
            print(f"Ensuring metadata storage path exists: {parent}")
            parent.mkdir(parents=True, exist_ok=True)

        artifacts_destination: str = demand_env_var(name="MLFLOW_ARTIFACTS_DESTINATION")
        print(f"Ensuring artifact storage path exists: {artifacts_destination}")
        Path(artifacts_destination).mkdir(parents=True, exist_ok=True)

    def _process_launch(self, shell_out_cmd: str) -> None:
        """
        Internal function for wrapping process launches.

        Parameters
        ----------
        shell_out_cmd: str
            The command to be executed.
        """

        args = shlex.split(shell_out_cmd)

        # Normally this would be leveraged within a context, however we are explicitly daemonize here.
        # pylint: disable=consider-using-with
        process = subprocess.Popen(args, stdout=subprocess.PIPE)
        for line in iter(process.stdout.readline, b""):
            print(line)

    def _process_launch_wait(self, shell_out_cmd: str) -> None:
        """
        Internal function for wrapping process launches [and waiting].

        Parameters
        ----------
        shell_out_cmd: str
            The command to be executed.
        """

        args = shlex.split(shell_out_cmd)

        with subprocess.Popen(args, stdout=subprocess.PIPE) as process:
            for line in iter(process.stdout.readline, b""):
                print(line)

    def launch_server(self, params: LaunchParameters) -> None:
        """
        This function is responsible for mapping AE5 arguments to mlflow launch arguments and then
        executing the service.

        Parameters
        ----------
        params: LaunchParameters
            Parameters needed for mlflow configuration.
        """

        if params.sanity:
            MLFlowTrackingServerController._ensure_sane_runtime_environment()

        # https://www.mlflow.org/docs/latest/cli.html#mlflow-server
        cmd: str = f"mlflow server --serve-artifacts --port {params.port} --host {params.address}"
        print(cmd)
        self._process_launch(shell_out_cmd=cmd)

    def execute(self, params: LaunchParameters) -> None:
        """
        Processes Managed MLFlow Tracking Server Activities.

        Parameters
        ----------
        params: LaunchParameters
            Parameters needed for mlflow configuration.
        """

        # Invoke the selected command
        if params.activity == ActivityType.SERVER:
            # Launch MLFlow Tracking Server
            self.launch_server(params=params)
        elif params.activity == ActivityType.GC:
            # Launch Garbage Collection Process
            self.perform_garbage_collection(dry_run=params.dry_run)
        elif params.activity == ActivityType.DB_UPGRADE:
            # Perform DB Upgrade
            self.perform_database_upgrade(dry_run=params.dry_run)
        else:
            message = f"launch type {params.activity} is not supported"
            raise ValueError(message)

    def perform_database_upgrade(self, dry_run: bool = True) -> None:
        """
        Performs MLFLow's internal database upgrade.

        !!! THIS PROCESS CAN CAUSE IRREVERSIBLE DAMAGE !!!

        Consult the MLFlow documentation prior to executing this method:
        https://mlflow.org/docs/latest/tracking.html#backend-stores

        Parameters
        ----------
        dry_run: bool
            Flag to control actually calling the backend process.
            Disabled by default.  The call must explicitly set `False`.
        """

        # https://mlflow.org/docs/latest/tracking.html#backend-stores
        cmd: str = f"mlflow db upgrade {demand_env_var(name='MLFLOW_BACKEND_STORE_URI')}"
        if dry_run:
            print("[DRY RUN] This process would start the database upgrade process.")
        else:
            print("Performing database upgrade")
            print(cmd)
            self._process_launch_wait(shell_out_cmd=cmd)

    def perform_garbage_collection(self, dry_run: bool = True) -> None:
        """
        From https://mlflow.org/docs/latest/cli.html#mlflow-gc :
        Permanently delete runs in the deleted lifecycle stage from the specified backend store.
        This command deletes all artifacts and metadata associated with the specified runs.

        !!! THIS PROCESS IS NOT REVERSIBLE !!!

        Consult the MLFlow documentation prior to executing this method:
        https://mlflow.org/docs/latest/cli.html#mlflow-gc

        Parameters
        ----------
        dry_run: bool
            Flag to control actually calling the backend process.
            Disabled by default.  The call must explicitly set `False`.
        """

        # https://mlflow.org/docs/latest/cli.html#mlflow-gc
        cmd: str = (
            "mlflow gc "
            f"--older-than {demand_env_var(name='MLFLOW_TRACKING_GC_TTL')} "
            f"--backend-store-uri {demand_env_var(name='MLFLOW_BACKEND_STORE_URI')}"
        )
        if dry_run:
            print("[DRY RUN] This process would remove all data in deleted the lifecycle state")
        else:
            print("Performing mlflow garbage collection")
            print(cmd)
            self._process_launch_wait(shell_out_cmd=cmd)
