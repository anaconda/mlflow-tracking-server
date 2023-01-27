#  Installation Guide

Overview
--------
Provides a hosted MLFlow Tracking Server meant for deployment into an Anaconda Enterprise environment.

Configuration
--------
The below variables control the configuration of the tracking server and related components.  See (Deployment) for information on when each is needed and created.

These should be defined as AE5 secrets within the service account running the tracking server.  Alternatively they can also be set within the `anaconda-project.yml` project files.

### Variables

1. `MLFLOW_BACKEND_STORE_URI`

    **Description**
    
    * SQLAlchemy compliant connection string
   
    **Details**
      * The backend store URI will most likely contain credentials for the connection and should not be exposed within anaconda-project.yml as plain text.
      * For additional details see: [SQLAlchemy - Engine Configuration](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls) and [MLFlow - Backend Stores](https://mlflow.org/docs/2.0.1/tracking.html#backend-stores).
   
    **Default**

    * sqlite:///data/mlflow/standalone/store/mydb.sqlite


2. `MLFLOW_ARTIFACTS_DESTINATION`

    **Description**
    
    * Artifact location storage URI
   
    **Details**
      * The artifact destination may not be sensitive and can be set as an ae5 secret for ease of configuration, or directly within the anaconda-project.yml for the tracking server project.
      * See [MLFlow Artifact Stores](https://mlflow.org/docs/2.0.1/tracking.html#artifact-stores) for supported stores (this can be as simple as a locally mounted volume).
   
    **Default**

    * data/mlflow/standalone/artifacts


4. `MLFLOW_TRACKING_URI`

    **Description**

    Remote Tracking Server URI 
   
    **Details**
      * This should be the static endpoint assigned to the private project deployment.


5. `MLFLOW_REGISTRY_URI`

    **Description**
    
    Model Registry URI
   
    **Details**
      * This should be the static endpoint assigned to the private project deployment.


6. `MLFLOW_TRACKING_TOKEN`

    **Description**
    
    AE5 Private Endpoint Access Token
   
    **Details**
      * This is used for authorization to the MLFLow services.


6. `MLFLOW_TRACKING_GC_TTL`

    **Description**
    
    MLFLow compliant string for the time limit
   
    **Details**
      * See [MLFlow Tracking Server Garbage Collection](https://mlflow.org/docs/2.0.1/cli.html?highlight=gc#mlflow-gc) and  [GC Older Than](https://mlflow.org/docs/2.0.1/cli.html?highlight=gc#cmdoption-mlflow-gc-older-than) for additional details.
   
    **Default**

    30d0h0m0s


Deployment
--------
1. **Create Dedicated Service Account**

    * The server **SHOULD** be uploaded and deployed using a dedicated service (ae5 user) account. 
   
   This allows for centralized configuration and management of the different components and isolation from other users.  Many of the configuration parameters can be set as ae5 secrets, and it is recommended to do so for most if not all of them in the following steps.

2. **Configure Python Environment**

    The deployment environment **MUST** occur within a conda environment with (at least):

        channels:
          - defaults
          - ae5-admin
        dependencies:
          - python=3
          - ae5-tools

3. **Configure AE5 Tools**

    Since the project needs to run under the user account created earlier we need to ensure we deploy to this user account.  This can be accomplished by either authenticating as the service account itself, or by an AE5 administrator who impersonates the service account at deployment time.  See [ae5-tools](https://github.com/Anaconda-Platform/ae5-tools) for additional details.
                    
4. **Download The Latest Release**

     The latest releases can be found [here](https://github.com/Anaconda-Platform/mlflow-tracking-server/releases/latest).

5. **[Optional] Slip Stream Customizations**
 
    The default works for most scenarios.  However, the archive can be updated and repackaged for specific deployments if needed. This could be useful in scenarios where changes to dependency versions, client specific commands, or default variables must occur prior to deployment.

6. **Upload Project**

    This can be accomplished using ae5 tools.

      **Example**
      > ae5 project upload --name "mlflow.tracking.server" mlflow.tracking.server.x.y.z.tar.gz

7. **[Optional] Disaster Recovery**

    If performing a disaster recover then at this point the data **MUST** be restored to the database and filesystem before moving to step 8.

8. **Deploy MLFlow Tracking Server**

   1. The below variables **MUST** be defined before deploying the server.

    | Variable                     |
    |------------------------------|
    | MLFLOW_BACKEND_STORE_URI     |
    | MLFLOW_ARTIFACTS_DESTINATION |

    2. To deploy an instance of the tracking server we deploy the project with the below options:
   * The `TrackingServer` command **MUST** be invoked.
   * The endpoint **SHOULD** be private.
   * A static name for the endpoint **SHOULD** be specified.

    This can be accomplished using ae5 tools.

    **Example**
    > ae5 project deploy --name "dev.mlflow.tracking.server" --endpoint "dev-mlflow-tracking-server" --command "TrackingServer" --private "dev.mlflow.tracking.server"

9. **Get Static URL For Endpoint**

    The static endpoint of the deployment is available from the deployment output.  It can also be found afterwards from the UI or by using the ae5 tools.

    **Example**
    > ae5 deployment info "mlflow-tracking-server"

10. **Store Static URL**

    The endpoint URLs will be needed within this service (ae5 user) account by the garbage collection process (and/or other consumers) and **SHOULD** be set as an ae5 secret.

    * If it is not set as an ae5 secret then it must be set within the `anaconda-project.yml` file when slip streaming (See Step 5) or by the consumer manually.

    **Both the tracking server and model registry should be set to the same endpoint:**

    | Variable            |
    |---------------------|
    | MLFLOW_TRACKING_URI |
    | MLFLOW_REGISTRY_URI |

11. **Create Private Deployment Token**

    If deployed using the recommended configuration, then the token will be **REQUIRED** to access the server API.  It can be found from the UI or by using the ae5 tools.

    **Example**
    > ae5 deployment token "mlflow.tracking.server"

12. **Store Private Deployment Token**

    * If using the stale artifact clean up process then this **MUST** be stored within an ae5 secret.
    * The token will be **REQUIRED** by all clients and users which need to access the MLFlow Tracking Service API.
    * The administrator of the MLFlow Tracking Server **MUST** generate and provide the access token **EVERY TIME** the server is restart.

    **Store the value:**

    |       Variable        |
    |-----------------------|
    | MLFLOW_TRACKING_TOKEN |

13. **Create Garbage Collection Schedule**

    What is garbage collection?

    The MLFlow Tracking Server does not automatically purge resources that a client deletes.  Instead, resources are set to the `deleted` lifecycle state and hidden from the UI and most API calls by default.  A deleted resource will block the creation of a new resource of the same name until the garbage collection process has purged it.  In order to purge deleted items a garbage collection process must be manually executed.

    * The project comes with a command for invoking garbage collection.  A schedule for the process **SHOULD** be created so that this is occurring regularly.
    
    * These environment variables **MUST** be defined as ae5 secrets, within the anaconda-project.yml, or passed to the ae5 job create command are variables (see below).

    | Variable                 |
    |--------------------------|
    | MLFLOW_BACKEND_STORE_URI |
    | MLFLOW_TRACKING_GC_TTL   |

    **Examples**

    > ae5 job create --command "GarbageCollection" --schedule "*/10 * * * *" --name "scheduled mlflow.tracking.server garbage collection" "mlflow.tracking.server"

    > ae5 job create --command "GarbageCollection" --schedule "*/10 * * * *" --name "scheduled mlflow.tracking.server garbage collection" "mlflow.tracking.server" --variable MLFLOW_TRACKING_GC_TTL="0d0h10m0s" --variable MLFLOW_BACKEND_STORE_URI="sqlite:///data/mlflow/dev/store/mydb.sqlite"

Automated Deployments
--------

* See [automation notebook](https://github.com/Anaconda-Platform/anaconda-enterprise-mlops-orchestration/blob/main/notebooks/deployment/tracking_server.ipynb) for an example.


Anaconda Project Runtime Commands
--------
These commands are used to start the server and perform the various administrative tasks.

| Command           | Environment | Description                                                    |
|-------------------|-------------|:---------------------------------------------------------------|
| TrackingServer    | Runtime     | Launches the MLFlow Tracking Server                            |
| GarbageCollection | Runtime     | Launches the MLFlow tracking server garbage collection process |
| DatabaseUpgrade   | Runtime     | Launches the MLFlow tracking server database upgrade process   |
