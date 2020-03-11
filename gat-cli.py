#!/usr/bin/env python3

import logging
import os
from typing import List, Optional, Tuple

import click
import tabulate

import gat


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("-v", "--verbose", count=True, help="Enable informational logging, use second time for debugging logs.")
@click.option(
    "-k",
    "--key",
    help="API key (can be also set in GAT_API_KEY environment variable)",
    default=lambda: os.environ.get("GAT_API_KEY", None),
    required=True,
)
@click.pass_context
def cli(context: click.Context, verbose: int, key: str) -> None:
    """
    Global App Testing command line client.
    """
    if verbose > 1:
        logging.basicConfig(level=logging.DEBUG)
    elif verbose > 0:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    context.obj = gat.GatApi(gat.GatApiConfiguration(key=key))


@cli.command()
@click.pass_context
def whoami(context: click.Context) -> None:
    """
    Show organization information.
    """
    api = context.obj
    organization = api.whoami()
    table = [["ID", "Name"], [organization.id, organization.name]]
    click.echo(tabulate.tabulate(table, headers="firstrow"))


@cli.command()
@click.pass_context
def list_applications(context: click.Context) -> None:
    """
    Show a list of applications.
    """
    api = context.obj
    table = [["ID", "Name", "Platform"]]
    table.extend([[application.id, application.name, application.platform_name] for application in api.applications()])
    click.echo(tabulate.tabulate(table, headers="firstrow"))


@cli.command()
@click.option("-a", "--application", "application_id", required=True, help="Application ID.")
@click.pass_context
def list_environments(context: click.Context, application_id: str) -> None:
    """
    Show a list of environments for the given application.
    """
    api = context.obj
    table = [["ID", "Name", "URL"]]
    application = api.application_by_id(application_id)
    table.extend([[environment.id, environment.name, environment.url] for environment in api.environments(application)])
    click.echo(tabulate.tabulate(table, headers="firstrow"))


@cli.command()
@click.option("-a", "--application", "application_id", required=True, help="Application ID.")
@click.argument("name")
@click.argument("url")
@click.pass_context
def create_environment(context: click.Context, application_id: str, name: str, url: str) -> None:
    """
    Create a new environment for the given application.
    """
    api = context.obj
    application = api.application_by_id(application_id)
    environment = api.create_environment(application, name, url)
    table = [["ID", "Name", "URL"], [environment.id, environment.name, environment.url]]
    click.echo(tabulate.tabulate(table, headers="firstrow"))


@cli.command()
@click.option("-a", "--application", "application_id", required=True, help="Application ID.")
@click.pass_context
def list_native_builds(context: click.Context, application_id: str) -> None:
    """
    Show a list of native builds for the given application.
    """
    api = context.obj
    table = [["ID", "Name", "Original file name", "External vendor URL", "Signing status"]]
    application = api.application_by_id(application_id)
    table.extend(
        [
            [build.id, build.name, build.original_file_name, build.external_vendor_url, build.signing_status]
            for build in api.native_builds(application)
        ]
    )
    click.echo(tabulate.tabulate(table, headers="firstrow"))


@cli.command()
@click.pass_context
def list_internet_browsers(context: click.Context) -> None:
    """
    List known Internet browsers.
    """
    api = context.obj
    table = [["ID", "Name", "Operating system"]]
    table.extend([[browser.id, browser.name, browser.operating_system_name] for browser in api.internet_browsers()])
    click.echo(tabulate.tabulate(table, headers="firstrow"))


@cli.command()
@click.pass_context
def list_mobile_devices(context: click.Context) -> None:
    """
    List known mobile devices.
    """
    api = context.obj
    table = [["ID", "Brand", "Name"]]
    table.extend([[device.id, device.brand_name, device.name] for device in api.mobile_devices()])
    click.echo(tabulate.tabulate(table, headers="firstrow"))


@cli.command()
@click.option("-a", "--application", "application_id", required=True, help="Application ID.")
@click.option("-b", "--batch", "test_case_runs_batch_id", required=True, help="Test case runs batch ID.")
@click.pass_context
def get_test_case_runs_batch_state(context: click.Context, application_id: str, test_case_runs_batch_id: str) -> None:
    """
    Show a state of a test case runs batch.
    """
    api = context.obj
    application = api.application_by_id(application_id)
    state = api.test_case_runs_batch_state(application, test_case_runs_batch_id)
    table = [
        ["ID", "State", "Total", "In progress", "Completed", "Failed", "Passed", "Cancelled"],
        [
            state.id,
            state.state,
            state.total_count,
            state.in_progress_count,
            state.completed_count,
            state.failed_count,
            state.passed_count,
            state.cancelled_count,
        ],
    ]
    click.echo(tabulate.tabulate(table, headers="firstrow"))


@cli.command()
@click.option("-a", "--application", "application_id", required=True, help="Application ID.")
@click.option("-b", "--batch", "test_case_runs_batch_id", required=True, help="Test case runs batch ID.")
@click.pass_context
def get_test_case_runs_batch_summary(context: click.Context, application_id: str, test_case_runs_batch_id: str) -> None:
    """
    Show a summary of a test case runs batch.
    """
    api = context.obj
    application = api.application_by_id(application_id)
    summary = api.test_case_runs_batch_summary(application, test_case_runs_batch_id)
    table = [
        ["ID", "Name", "Started", "Finished", "Credits", "Testers involved"],
        [
            summary.id,
            summary.name,
            summary.start_time,
            summary.finish_time,
            summary.test_case_credits,
            summary.testers_involved,
        ],
    ]
    click.echo(tabulate.tabulate(table, headers="firstrow"))
    click.echo("\nTest case runs:")

    table = [["ID", "Name", "Ada URL", "Failed results", "Passed results", "Total results"]]
    for test_case_run in summary.test_case_runs:
        table.append(
            [
                test_case_run.id,
                test_case_run.name,
                test_case_run.ada_url,
                test_case_run.failed_results_count,
                test_case_run.passed_results_count,
                test_case_run.total_results_count,
            ]
        )
    click.echo(tabulate.tabulate(table, headers="firstrow"))


@cli.command()
@click.option("-a", "--application", "application_id", required=True, help="Application ID.")
@click.option("-e", "--environment", "environment_id", required=True, help="Environment ID.")
@click.option(
    "-b",
    "--browser",
    "internet_browser_ids",
    required=True,
    multiple=True,
    help="Internet browser ID (can be used multiple times).",
)
@click.option(
    "-t",
    "--test-case",
    "test_case_ids",
    required=True,
    multiple=True,
    help="Test case ID to run (can be used multiple times).",
)
@click.pass_context
def create_test_case_runs_batch(
    context: click.Context,
    application_id: str,
    environment_id: str,
    internet_browser_ids: List[str],
    test_case_ids: List[str],
) -> None:
    """
    Create a new test case runs batch; run given test cases as a new batch.
    """
    api = context.obj

    application = api.application_by_id(application_id)
    environment = api.environment_by_id(application, environment_id)
    internet_browser = [ib for ib in api.internet_browsers() if ib.id in internet_browser_ids]
    if len(internet_browser_ids) != len(internet_browser):
        click.echo("Error: not all internet browser IDs matched")
        return
    test_cases = [tc for tc in api.test_cases(application) if tc.id in test_case_ids]
    if len(test_case_ids) != len(test_cases):
        click.echo("Error: not all test case IDs matched")
        return

    test_case_runs_batch = api.create_test_case_runs_batch(application, environment, internet_browser, test_cases)
    table = [["ID"], [test_case_runs_batch.id]]
    click.echo(tabulate.tabulate(table, headers="firstrow"))


@cli.command()
@click.option("-a", "--application", "application_id", required=True, help="Application ID.")
@click.pass_context
def list_test_cases(context: click.Context, application_id: str) -> None:
    """
    List test cases for given application.
    """
    api = context.obj
    application = api.application_by_id(application_id)
    table = [["ID", "Title", "Importance", "Section"]]
    table.extend(
        [
            [test_case.id, test_case.title, test_case.importance, test_case.section]
            for test_case in api.test_cases(application)
        ]
    )
    click.echo(tabulate.tabulate(table, headers="firstrow"))


@cli.command()
@click.option("-a", "--application", "application_id", required=True, help="Application ID.")
@click.pass_context
def delete_test_cases(context: click.Context, application_id: str) -> None:
    """
    Delete ALL test cases for given application.
    """
    api = context.obj
    application = api.application_by_id(application_id)
    api.delete_all_test_cases(application)
    click.echo(f"All test cases deleted for application {application.name}")


@cli.command()
@click.option("-a", "--application", "application_id", required=True, help="Application ID.")
@click.option(
    "-i",
    "--importance",
    "importance",
    default="Medium",
    type=click.Choice(["Low", "Medium", "Critical"], case_sensitive=False),
    help="Importance of a new test case",
)
@click.option("-s", "--section", "section", default=None, help="Section name for the new test case")
@click.argument("title")
@click.argument("instruction", nargs=-1)
@click.pass_context
def create_test_case(
    context: click.Context,
    application_id: str,
    importance: Optional[str],
    section: Optional[str],
    title: str,
    instruction: Tuple[str],
) -> None:
    """
    Create new test case with instructions.

    Each instruction ending with a question mark will be treated as an assertion.
    """
    api = context.obj
    application = api.application_by_id(application_id)

    instructions = [
        gat.TestCaseInstruction(id="new", content=instruction_text, assertion=instruction_text.endswith("?"))
        for instruction_text in instruction
    ]
    test_case = gat.TestCase(id="new", title=title, importance=importance, section=section, instructions=instructions)

    created_test_case = api.create_test_cases(application, [test_case])[0]
    table = [
        ["ID", "Title", "Importance", "Section"],
        [created_test_case.id, created_test_case.title, created_test_case.importance, created_test_case.section],
    ]
    click.echo(tabulate.tabulate(table, headers="firstrow"))


if __name__ == "__main__":
    cli(obj=None)
