#!/usr/bin/env python3

import datetime
import json
import logging
import os
import time
from typing import Any, Dict, IO, List, Optional, Tuple

from .data import (
    Application,
    Country,
    Environment,
    GatApiConfiguration,
    InternetBrowser,
    MobileDevice,
    NativeBuild,
    Organization,
    TestCase,
    TestCaseInstruction,
    TestCaseRun,
    TestCaseRunsBatch,
    TestCaseRunsBatchState,
    TestCaseRunsBatchSummary,
    TestCaseRunsBatchTestCaseRun,
)


class GatError(BaseException):
    pass


class GatApi:
    def __init__(self, configuration: GatApiConfiguration):
        self.__configuration = configuration
        self.__logger = logging.getLogger("gat.GatApi")
        self.__logger.debug("Using key: %s...%s", self.__configuration.key[:4], self.__configuration.key[-4:])

    def __call(
        self,
        method: str,
        suffix: str,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:

        final_url = os.path.join(self.__configuration.uri, suffix)
        self.__logger.info("Final URI: %s", final_url)
        if json_data:
            self.__logger.debug("Data:\n%s", json.dumps(json_data, sort_keys=True, indent=2))

        headers = headers or {"Content-Type": "application/vnd.api+json"} if data else {}
        start_time = time.time()
        response = self.__configuration.session.request(
            method, final_url, headers=headers, json=json_data, data=data, files=files
        )
        elapsed_time = time.time() - start_time
        self.__logger.info("Response status code: %d, in %.3f sec", response.status_code, elapsed_time)
        if response.status_code in [200, 201] and "application/vnd.api+json" in response.headers["Content-Type"]:
            json_response = response.json()
            self.__logger.debug("Returned JSON data:\n%s", json.dumps(json_response, sort_keys=True, indent=2))
            return json_response
        elif response.status_code in [200, 201]:
            text_data = response.text
            self.__logger.debug("Returned text data:\n%s", text_data)
            return text_data
        elif response.status_code == 204:
            return
        elif 400 <= response.status_code < 500 and "errors" in response.json():
            first_error = response.json()["errors"][0]
            error_message = first_error["title"]
            if "detail" in first_error:
                error_message = f"{error_message} - {first_error['detail']}"
            raise GatError(f"Call failed: {response.status_code}: {error_message}")
        raise GatError(f"Call failed: {response.status_code}")

    @staticmethod
    def __parse_time(string_time: Optional[str]) -> Optional[datetime.datetime]:
        return datetime.datetime.fromisoformat(string_time.replace("Z", "+00:00")) if string_time else None

    def whoami(self) -> Organization:
        organization_data = self.__call("GET", "whoami")["data"]
        return Organization(id=organization_data["id"], name=organization_data["attributes"]["name"])

    def applications(self) -> List[Application]:
        return [
            Application(id=app["id"], name=app["attributes"]["name"], platform_name=app["attributes"]["platformName"])
            for app in self.__call("GET", "applications")["data"]
        ]

    def application_by_id(self, id: str) -> Application:
        try:
            return next(application for application in self.applications() if application.id == id)
        except StopIteration as stop_iteration:
            raise GatError(f"No application with ID {id}") from stop_iteration

    def environments(self, application: Application) -> List[Environment]:
        return [
            Environment(id=env["id"], name=env["attributes"]["name"], url=env["attributes"]["url"])
            for env in self.__call("GET", f"applications/{application.id}/environments")["data"]
        ]

    def environment_by_id(self, application: Application, id: str) -> Environment:
        try:
            return next(environment for environment in self.environments(application) if environment.id == id)
        except StopIteration as stop_iteration:
            raise GatError(f"No environment with ID {id}") from stop_iteration

    def create_environment(self, application: Application, name: str, url: str) -> Environment:
        new_env = self.__call(
            "POST",
            f"applications/{application.id}/environments",
            json_data={"data": {"type": "applicationEnvironment", "attributes": {"name": name, "url": url}}},
        )["data"]
        return Environment(id=new_env["id"], name=new_env["attributes"]["name"], url=new_env["attributes"]["url"])

    def delete_environment(self, application: Application, environment: Environment):
        self.__call("DELETE", f"applications/{application.id}/environments/{environment.id}")

    def update_environment(
        self, application: Application, environment: Environment, name: str, url: str
    ) -> Environment:
        new_env = self.__call(
            "PATCH",
            f"applications/{application.id}/environments/{environment.id}",
            json_data={"data": {"type": "applicationEnvironment", "attributes": {"name": name, "url": url}}},
        )["data"]
        return Environment(id=new_env["id"], name=new_env["attributes"]["name"], url=new_env["attributes"]["url"])

    def native_builds(self, application: Application) -> List[NativeBuild]:
        return [
            NativeBuild(
                id=build["id"],
                name=build["attributes"]["name"],
                original_file_name=build["attributes"].get("appFileOriginalFilename"),
                external_vendor_url=build["attributes"].get("externalVendorUrl"),
                signing_status=build["attributes"]["signingStatus"],
            )
            for build in self.__call("GET", f"applications/{application.id}/native_application_builds")["data"]
        ]

    def native_build_by_id(self, application: Application, id: str) -> NativeBuild:
        try:
            return next(native_build for native_build in self.native_builds(application) if native_build.id == id)
        except StopIteration as stop_iteration:
            raise GatError(f"No native build with ID {id}") from stop_iteration

    def delete_native_build(self, application: Application, id: str):
        self.__call("DELETE", f"applications/{application.id}/native_application_builds/{id}")

    def update_native_build(self, application: Application, native_build: NativeBuild, name: str) -> NativeBuild:
        new_build = self.__call(
            "PATCH",
            f"applications/{application.id}/native_application_builds/{native_build.id}",
            json_data={"data": {"type": "nativeApplicationBuild", "attributes": {"name": name}}},
        )["data"]

        return NativeBuild(
            id=new_build["id"],
            name=new_build["attributes"]["name"],
            original_file_name=new_build["attributes"].get("appFileOriginalFilename"),
            external_vendor_url=new_build["attributes"].get("externalVendorUrl"),
            signing_status=new_build["attributes"]["signingStatus"],
        )

    def create_native_build(self, application: Application, name: str, build: str) -> NativeBuild:
        files = None
        external_vendor_url = None

        if self.__is_url(build):
            external_vendor_url = build
        else:
            files = self.__get_files(build)

        new_build = self.__call(
            "POST",
            f"applications/{application.id}/native_application_builds",
            data={
                "data[type]": "nativeApplicationBuild",
                "data[attributes][name]": name,
                "data[attributes][external_vendor_url]": external_vendor_url,
            },
            headers=self.__get_headers_with_content_type(build),
            files=files,
        )["data"]

        return NativeBuild(
            id=new_build["id"],
            name=new_build["attributes"]["name"],
            original_file_name=new_build["attributes"].get("appFileOriginalFilename"),
            external_vendor_url=new_build["attributes"].get("externalVendorUrl"),
            signing_status=new_build["attributes"]["signingStatus"],
        )

    @staticmethod
    def __is_url(build: str) -> bool:
        return build.startswith("http")

    @staticmethod
    def __get_files(path: str) -> List[Tuple[str, IO]]:
        return [("data[attributes][app_file]", open(path, "rb"))]

    def __get_headers_with_content_type(self, build: str) -> Dict[str, str]:
        return {"Content-Type": "multipart/form-data"} if self.__is_url(build) else {}

    def internet_browsers(self) -> List[InternetBrowser]:
        return [
            InternetBrowser(
                id=ib["id"],
                name=ib["attributes"]["name"],
                operating_system_name=ib["attributes"]["operatingSystemName"],
            )
            for ib in self.__call("GET", "internet_browsers")["data"]
        ]

    def mobile_devices(self) -> List[MobileDevice]:
        return [
            MobileDevice(id=md["id"], name=md["attributes"]["name"], brand_name=md["attributes"]["brandName"])
            for md in self.__call("GET", "mobile_devices")["data"]
        ]

    def test_case_runs_batch_state(self, application: Application, id: str) -> TestCaseRunsBatchState:
        state_data = self.__call("GET", f"applications/{application.id}/test_case_runs_batches/{id}/state")["data"]
        return TestCaseRunsBatchState(
            id=state_data["id"],
            state=state_data["attributes"]["state"],
            total_count=state_data["attributes"]["totalCount"],
            in_progress_count=state_data["attributes"]["inProgressCount"],
            completed_count=state_data["attributes"]["completedCount"],
            failed_count=state_data["attributes"]["failedCount"],
            passed_count=state_data["attributes"]["passedCount"],
            cancelled_count=state_data["attributes"]["cancelledCount"],
        )

    def test_case_runs_batch_summary(self, application: Application, id: str) -> TestCaseRunsBatchSummary:
        summary_response = self.__call("GET", f"applications/{application.id}/test_case_runs_batches/{id}/summary")

        summary_data = summary_response["data"]
        return TestCaseRunsBatchSummary(
            id=summary_data["id"],
            name=summary_data["attributes"]["name"],
            start_time=GatApi.__parse_time(summary_data["attributes"]["startTime"]),
            finish_time=GatApi.__parse_time(summary_data["attributes"]["finishTime"]),
            test_case_credits=summary_data["attributes"]["testCaseCredits"],
            testers_involved=summary_data["attributes"]["testersInvolved"],
            application_id=summary_data["relationships"]["application"]["data"]["id"],
            environment_id=summary_data["relationships"]["environment"]["data"]["id"],
            test_case_runs=[
                TestCaseRunsBatchTestCaseRun(
                    id=data["id"],
                    name=data["attributes"]["name"],
                    ada_url=data["attributes"]["adaUrl"],
                    failed_results_count=data["attributes"]["failedResultsCount"],
                    passed_results_count=data["attributes"]["passedResultsCount"],
                    total_results_count=data["attributes"]["totalResultsCount"],
                )
                for data in summary_response["included"][0]["data"]
            ],
        )

    def create_test_case_runs_batch(
        self,
        application: Application,
        environment: Environment,
        internet_browsers: List[InternetBrowser],
        test_cases: List[TestCase],
    ) -> TestCaseRunsBatch:
        data = {
            "data": {
                "type": "testCaseRunsBatch",
                "attributes": {},
                "relationships": {
                    "applicationEnvironment": {"data": {"type": "applicationEnvironment", "id": environment.id}},
                    "internetBrowsers": {
                        "data": [{"type": "internetBrowser", "id": ib.id} for ib in internet_browsers]
                    },
                    "testCases": {"data": [{"type": "testCase", "id": tc.id} for tc in test_cases]},
                },
            }
        }
        test_case_runs_batch_data = self.__call(
            "POST", f"applications/{application.id}/test_case_runs_batches", json_data=data
        )["data"]

        return TestCaseRunsBatch(id=test_case_runs_batch_data["id"])

    def test_cases(self, application: Application) -> List[TestCase]:
        return [
            # TODO: Populate importance and section when available
            TestCase(
                id=test_case["id"],
                title=test_case["attributes"]["title"],
                importance=None,
                section=None,
                instructions=[],
            )
            for test_case in self.__call("GET", f"applications/{application.id}/test_cases")["data"]
        ]

    def delete_all_test_cases(self, application: Application):
        self.__call("DELETE", f"applications/{application.id}/test_cases/delete_all")

    def delete_test_cases(self, application: Application, ids: List[str]):
        self.__call("DELETE", f"applications/{application.id}/test_cases?ids={','.join(ids)}")

    def create_test_cases(self, application: Application, test_cases: List[TestCase]) -> List[TestCase]:
        data = []
        for test_case in test_cases:
            data.append(
                {
                    "type": test_case.type,
                    "attributes": {
                        "title": test_case.title,
                        "importance": test_case.importance,
                        "section": test_case.section,
                        "instructions": [
                            {"type": i.type, "id": i.id}
                            if i.type == "testCase"
                            else {"type": i.type, "attributes": {"content": i.content, "assertion": i.assertion}}
                            for i in test_case.instructions
                        ],
                    },
                }
            )

        return [
            TestCase(
                id=test_case["id"],
                title=test_case["attributes"]["title"],
                importance=test_case["attributes"]["importance"],
                section=test_case["attributes"]["section"],
                instructions=[
                    TestCaseInstruction(
                        id=i["id"], content=i["attributes"]["content"], assertion=i["attributes"]["assertion"]
                    )
                    for i in test_case["attributes"]["instructions"]
                ],
            )
            for test_case in self.__call(
                "POST", f"applications/{application.id}/test_cases/import", json_data={"data": data}
            )["data"]
        ]

    def countries(self) -> List[Country]:
        return [
            Country(
                id=country["id"],
                name=country["attributes"]["name"],
                code=country["attributes"]["code"],
                available_platforms=country["attributes"]["availablePlatforms"],
            )
            for country in self.__call("GET", "countries")["data"]
        ]

    def test_case_runs(
        self,
        application: Application,
        batch_id: str,
        test_case_run_ids: Optional[List[str]],
        outcome: Optional[str],
        importance: Optional[str],
    ) -> List[TestCaseRun]:
        filters = [
            f"filter[{key}]={value}"
            for key, value in {"ids": test_case_run_ids, "outcome": outcome, "importance": importance}.items()
            if value
        ]

        result = self.__call(
            "GET",
            f"applications/{application.id}/test_case_runs_batches/{batch_id}/test_case_runs"
            f"{('?' + '&'.join(filters)) if filters else ''}",
        )

        return [
            TestCaseRun(
                id=test_case_run["id"],
                test_case_name=test_case_run["attributes"]["testCaseName"],
                test_case_section=test_case_run["attributes"]["testCaseSection"],
                test_case_importance=test_case_run["attributes"]["testCaseImportance"],
                ada_url=test_case_run["attributes"]["adaUrl"],
                variations=[
                    TestCaseRun.Variation(
                        name=variation["name"],
                        results=[
                            TestCaseRun.Variation.TestCaseRunResult(
                                outcome=result["outcome"],
                                attachment_url=result.get("attachmentUrl"),
                                tester_comment=result["testerComment"],
                                steps_to_reproduce=result["stepsToReproduce"],
                                reported_at=GatApi.__parse_time(result["reportedAt"]),
                                country=result["country"],
                            )
                            for result in variation["results"]
                        ],
                    )
                    for variation in test_case_run["attributes"]["variations"]
                ],
            )
            for test_case_run in result["data"]
        ]
