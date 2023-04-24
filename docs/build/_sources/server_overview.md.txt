# MLFlow Tracking Server Overview

The recommended way to deploy an MLFlow Tracking Server directly within an AE5 instance is with proxied artifact mode.  

* In practice this simplifies, unifies, and limits access to (metadata and models) allowing the tracking server to act as the source of truth for experimentation tracking and model storage.
* The alternatives require clients to have read/write access to the backend artifact storage system.  Not putting an API in front of this can lead to catastrophic data loss (e.g. user error, etc.) and is not recommended.  The tracking server supports “file system only access“ deployments and many other configurations to accommodate edge cases.


## Tracking Server

### Assumptions

* Operate in proxied artifact mode.  See [MLflow Tracking — MLflow 2.3.0 documentation](https://www.mlflow.org/docs/2.3.0/tracking.html#scenario-5-mlflow-tracking-server-enabled-with-proxied-artifact-storage-access) for additional details.
* Run as a private deployment.
* Deployed with a static URL.
* Storage is on a persistence volume, or location such as in data.
* An external database is used for metadata persistence.

<img src="_static/MLFlow Tracking Server Deployment Diagram.png" alt="Tracking Server With Proxied Artifact Access">

The tracking server has two types of assets (metadata, and artifacts).

### Metadata

Metadata can be persisted to any backend supported by SQLAlchemy, and the server itself uses a SQLAlchemy compliant connection string for this configuration parameter. 
* See [Where Runs Are Recorded](https://www.mlflow.org/docs/2.3.0/tracking.html#where-runs-are-recorded)  for details on all supported configurations.  
* For additional details on SQLAlchemy see: [Database URLs](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls).

### File Assets

* File assets are stored on a file system accessible to the server at runtime.  See [Artifact Stores](https://www.mlflow.org/docs/2.3.0/tracking.html#artifact-stores)  for details on all supported configurations.

### Backup Strategy

* Standard backup and verification practices **SHOULD** be followed that meet the business continuity requirements of the organization.
* Since the MLFlow Tracking Server uses two different storage systems, backups **MUST** be synchronized between the two systems to ensure recoverability.

### Upgrades

* MLFlow has a schema upgrade mechanism for its database. See [DB Upgrade](https://mlflow.org/docs/2.3.0/cli.html?highlight=schema#mlflow-db) for the documented process and its caveats.  Specifically ensure that backups of the data tier exist and are usable as the process can be destructive and is not reversible.

### Disaster Recovery

* Details on when to restore data during disaster recovery are included within the [Installation Guide](installation_guide.md).

### Current Limitations

* UI must be `popped out` of iframe. (Lack of CORS permissions involving iframing the UI causes the UI to be unusable)
  * [mlflow UI not working in iframe[BUG]--cross origin issue · Issue #3583 · mlflow/mlflow](https://github.com/mlflow/mlflow/issues/3583)
* MLFlow does NOT have any authentication/authorization mechanism.  We leverage AE5’s authorization mechanism to secure it. (e.g. private deployment, with token access for API consumption)
* Possible performance issues with large numbers of experiments ([MLflow worker timeout when opening UI · Issue #925 · mlflow/mlflow](https://github.com/mlflow/mlflow/issues/925))
