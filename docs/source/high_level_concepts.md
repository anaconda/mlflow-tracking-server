# High Level Concepts

Tracking Server, Workflows, and Endpoints can all run as deployments natively within Anaconda Enterprise.

Below we can see the deployment and access pattern for MLFlow Tracking Server within Anaconda Enterprise.
<img src="_static/AE5 MLFlow High Level.png" alt="AE5 MLFlow High Level Diagram">
In the following sections we will go into further detail on each tier within the diagram.

## Consumers

Consumers are internal or external to the platform.  Both types of consumers must authenticate against the deployed resources in the same way, since there is no implicit trust.

<img src="_static/AE5 MLFlow High Level Consumers.png" alt="Consumers">

**External Consumer Examples**

* Users directly accessing the MLFlow Tracking Server, triggering project runs, or accessing model endpoints.

**Internal Consumer Examples**

* AE5 hosted notebook instances or workflows which interact with the MLFlow tracking server for tracking, or reporting.

## AE5 Platform

Anaconda Enterprise provides authentication, and compute for notebooks, endpoints, workflows, and the tracking server.

<img src="_static/AE5 MLFlow High Level Platform.png" alt="AE5">

## Data Tier

Since the system must persist information (e.g. experiments, runs, models) storage is required.  This takes the form of filesystems and databases.

<img src="_static/AE5 MLFlow High Level Data Tier.png" alt="Data Tier]">

### Other Data Tier Considerations

* External data sources which feed into or out of the platform
* Access to the data versioning mechanism
