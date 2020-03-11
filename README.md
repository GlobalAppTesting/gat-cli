# CLI for Global App Testing API

* API location: <https://app.globalapptesting.com/api/>
* API documentation: <https://app.globalapptesting.com/api/api_docs>
* Swagger/OpenAPI specification: <https://app.globalapptesting.com/api/swagger_doc>

To make use of the API you are required to be a customer of Global App Testing and have access to our self-service testing platform, Ada at <https://app.globalapptesting.com/>. Please visit <https://www.globalapptesting.com/> to find out about our best-in-class web & app testing services.

## Using the CLI client

This client is written in Python, the majority of the code is located in `gat` directory and the command line interface itself is in `gat-cli.py` file. [poetry](https://python-poetry.org/) is used for dependency management, installation instructions are available in [poetry documentation](https://python-poetry.org/docs/).

There are two ways of running the client: directly using `poetry` and using Docker image. In both cases you need to either specify `--key` option or set `GAT_API_KEY` environment variable to contain a valid API access key.

### Using `poetry`

To run the client checkout the repository and install required dependencies using `poetry`:

```shell
$ poetry install --no-dev
Installing dependencies from lock file


Package operations: 7 installs, 0 updates, 0 removals

  - Installing certifi (2019.11.28)
  - Installing chardet (3.0.4)
  - Installing idna (2.9)
  - Installing urllib3 (1.25.8)
  - Installing click (7.0)
  - Installing requests (2.23.0)
  - Installing tabulate (0.8.6)
```

Note that the exact package versions can differ from the output shown above. After the installation you can run the client using `poetry`:

```shell
$ poetry run python gat-cli.py
Usage: gat-cli.py [OPTIONS] COMMAND [ARGS]...
[ ... ]
```

If you have a valid API key use `whoami` command to validate access:

```shell
$ poetry run python gat-cli.py whoami
ID                                            Name
--------------------------------------------  ------------------
qFS3RrkAE8K5vF1-U43ICPRnlJCfmnNwX3scTLmmG4w=  GAT QA Engineering
$ poetry run python gat-cli.py --key="${GAT_API_KEY}" whoami
ID                                            Name
--------------------------------------------  ------------------
qFS3RrkAE8K5vF1-U43ICPRnlJCfmnNwX3scTLmmG4w=  GAT QA Engineering
```

You can also access the virtual environment directly:

```shell
$ poetry shell
[ ... ]
$ ./gat-cli.py whoami
ID                                            Name
--------------------------------------------  ------------------
qFS3RrkAE8K5vF1-U43ICPRnlJCfmnNwX3scTLmmG4w=  GAT QA Engineering
```

### Using Docker

Docker image wraps around `python:3.7-alpine` and `poetry`, to build it:

```shell
$ docker build -t gat-cli:latest .
Sending build context to Docker daemon  61.95kB
Step 1/14 : FROM python:3.7-alpine AS dev
[ ... ]
Removing intermediate container f5cbe382592b
 ---> 9db8de7d4b08
Successfully built 9db8de7d4b08
Successfully tagged gat-cli:latest
```

Running also requires passing a valid API key using either environment or `--key` option:

```shell
$ docker run --rm -it -e "GAT_API_KEY=${GAT_API_KEY}" gat-cli whoami
ID                                            Name
--------------------------------------------  ------------------
qFS3RrkAE8K5vF1-U43ICPRnlJCfmnNwX3scTLmmG4w=  GAT QA Engineering
$ docker run --rm -it gat-cli --key="${GAT_API_KEY}" whoami
ID                                            Name
--------------------------------------------  ------------------
qFS3RrkAE8K5vF1-U43ICPRnlJCfmnNwX3scTLmmG4w=  GAT QA Engineering
```

## Available commands

List of available commands is accessible by invoking the client without any specific command or by using `--help`. Note that the output of `--help` depends on the command and shows more details if it follows a command:

```shell
$ poetry run python gat-cli.py --help
Usage: gat-cli.py [OPTIONS] COMMAND [ARGS]...

  Global App Testing command line client.

Options:
  -v, --verbose   Enable informational logging, use second time for debugging
                  logs.
  -k, --key TEXT  API key (can be also set in GAT_API_KEY environment
                  variable)  [required]
  -h, --help      Show this message and exit.

Commands:
  create-environment              Create a new environment for the given...
  create-test-case                Create new test case with instructions.
  create-test-case-runs-batch     Create a new test case runs batch; run...
  delete-test-cases               Delete ALL test cases for given...
  get-test-case-runs-batch-state  Show a state of a test case runs batch.
  get-test-case-runs-batch-summary
                                  Show a summary of a test case runs...
  list-applications               Show a list of applications.
  list-environments               Show a list of environments for the...
  list-internet-browsers          List known Internet browsers.
  list-mobile-devices             List known mobile devices.
  list-native-builds              Show a list of native builds for the...
  list-test-cases                 List test cases for given application.
  whoami                          Show organization information.
$ poetry run python gat-cli.py whoami --help
Usage: gat-cli.py whoami [OPTIONS]

  Show organization information.

Options:
  -h, --help  Show this message and exit.
```

Positioning of options and arguments does matter, compare:

```shell
$ poetry run python gat-cli.py -v whoami
INFO:gat.GatApi:Final URI: https://app.globalapptesting.com/api/v1/whoami
INFO:gat.GatApi:Response status code: 200, in 0.262 sec
ID                                            Name
--------------------------------------------  ------------------
qFS3RrkAE8K5vF1-U43ICPRnlJCfmnNwX3scTLmmG4w=  GAT QA Engineering
$ poetry run python gat-cli.py whoami -v
Usage: gat-cli.py whoami [OPTIONS]
Try "gat-cli.py whoami -h" for help.

Error: no such option: -v
```

Global options need to be provided before the command, command-specific options after the command.

## License

This code is published under the terms of the [3-Clause BSD License](https://opensource.org/licenses/BSD-3-Clause), the full text can be found in `LICENSE` file.
