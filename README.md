# LCA Assembly Service

# Introduction

This repo is a [git submodule](https://git-scm.com/book/en/v2/Git-Tools-Submodules). Thus changes made here will be
reflected in external sources, which requires a certain workflow to ensure consistency for all developers who depend on
this repo.
Besides that it functions as any other repo.

# Getting Started

To get started please make sure that the following pieces of software are installed on your machine.

# Software dependencies

## Windows

- [WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10)
- [Docker](https://docs.docker.com/desktop/windows/install/)
- [Minikube](https://minikube.sigs.k8s.io/docs/start/)
- [Skaffold](https://skaffold.dev/docs/install/#standalone-binary)
- Python 3.10
- [pipenv](https://pipenv.pypa.io/en/latest/#install-pipenv-today)
- [pre-commit](https://pre-commit.com/#installation)

## Linux

- [Docker](https://docs.docker.com/engine/install/ubuntu/)
- [Minikube](https://minikube.sigs.k8s.io/docs/start/)
- [Skaffold](https://skaffold.dev/docs/install/#standalone-binary)
- Python 3.10
- [pipenv](https://pipenv.pypa.io/en/latest/#install-pipenv-today)
- [pre-commit](https://pre-commit.com/#installation)

## Getting the backend up and running

**Setup local `.env`**
Copy the contents of `.env.example` to a local `.env` file.
To get the `ARTIFACTS_TOKEN_BACKEND_PACKAGES` token for fetching python packages
from [Azure Artifacts](https://dev.azure.com/arkitema/lca-platform/_artifacts/feed/backend-packages).
You can do it by creating a PAT that have read access to artifacts.

**Install dependencies**
```shell
# Set environment variables on linux
export ARTIFACTS_TOKEN_BACKEND_PACKAGES=<YOUR_PAT>

# Set environment variables on Windows
$env:ARTIFACTS_TOKEN_BACKEND_PACKAGES=<YOUR_PAT>
# Install packages
pipenv install --dev

# Install pre-commit hooks
pre-commit install
```

See more about Windows Env vars [here](https://www.tutorialspoint.com/how-to-set-environment-variables-using-powershell)
**Start dev server**

```shell
# Start Minikube to run a local Kubernetes cluster
minikube start
# Run Skaffold
skaffold dev
```

**Run tests locally**

```shell
pytest tests/
```

**Make migration**
Skaffold should be running!

```shell
./local_migration.sh
```

**Export GraphQL schema**

```shell
./export_schema.sh
```

**Load EPD data into database**

```shell
kubectl -n assembly exec -it $(kubectl -n assembly get pod -l app=backend -o name) -- python src/import_data/main.py
```

# Folder Structure

```plaintext
alembic/  # Contains migrations
graphql/  # Contains graphql schema for the gateway
helm/  # helm chart for deployment
src/  # source code
    core/  # code related to FastAPI/webserver
    exceptions/  # custom exceptions
    models/  # database models
    routes/  # api routes
    schema/  # graphql schema definitions
tests/  # test code
```

# Documentation

* [FastAPI](https://fastapi.tiangolo.com/)
* [Strawberry](https://strawberry.rocks/docs)
* [SQLModel](https://sqlmodel.tiangolo.com/)
* [Alembic](https://alembic.sqlalchemy.org/en/latest/)
* [Pytest](https://docs.pytest.org/en/7.1.x/)


# License

Unless otherwise described, the code in this repository is licensed under the Apache-2.0 License. Please note that some
modules, extensions or code herein might be otherwise licensed. This is indicated either in the root of the containing
folder under a different license file, or in the respective file's header. If you have any questions, don't hesitate to
get in touch with us via [email](mailto:chrk@arkitema.com).