""" Anaconda Enterprise Service Wrapper Definition """
import sys
from argparse import ArgumentParser, Namespace

from .common.secrets import load_ae5_user_secrets
from .contracts.dto.launch_parameters import LaunchParameters
from .controller import MLFlowTrackingServerController

if __name__ == "__main__":
    # This function is meant to provide a handler mechanism between the AE5 deployment arguments
    # and those required by the called process (or service).

    # arg parser for the standard anaconda-project options
    parser = ArgumentParser(
        prog="mlflow-tracking-server-launch-wrapper", description="mlflow tracking server launch wrapper"
    )
    parser.add_argument("--anaconda-project-host", action="append", default=[], help="Hostname to allow in requests")
    parser.add_argument("--anaconda-project-port", action="store", default=8086, type=int, help="Port to listen on")
    parser.add_argument(
        "--anaconda-project-iframe-hosts",
        action="append",
        help="Space-separated hosts which can embed us in an iframe per our Content-Security-Policy",
    )
    parser.add_argument(
        "--anaconda-project-no-browser", action="store_true", default=False, help="Disable opening in a browser"
    )
    parser.add_argument(
        "--anaconda-project-use-xheaders", action="store_true", default=False, help="Trust X-headers from reverse proxy"
    )
    parser.add_argument("--anaconda-project-url-prefix", action="store", default="", help="Prefix in front of urls")
    parser.add_argument(
        "--anaconda-project-address",
        action="store",
        default="0.0.0.0",
        help="IP address the application should listen on",
    )

    parser.add_argument(
        "--ensure-sane-env",
        action="store_true",
        default=False,
        help="Create runtime file system structures required by mlflow.  Should be used for local only modes.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Flag for controlling actual application of the system level change",
    )
    parser.add_argument(
        "--activity",
        action="store",
        type=str,
        choices=["server", "gc", "db_upgrade"],
        help="The function (server, gc, db upgrade) to perform",
    )

    # Load command line arguments
    args: Namespace = parser.parse_args(sys.argv[1:])
    print(args)

    # Load defined environmental variables
    load_ae5_user_secrets(silent=False)

    # Create our controller
    controller: MLFlowTrackingServerController = MLFlowTrackingServerController()

    # Build launch parameters
    params: LaunchParameters = LaunchParameters(
        activity=args.activity,
        sanity=args.ensure_sane_env,
        port=args.anaconda_project_port,
        address=args.anaconda_project_address,
        dry_run=args.dry_run,
    )

    # Execute the request
    controller.execute(params=params)
