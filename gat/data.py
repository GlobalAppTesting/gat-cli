#!/usr/bin/env python3

import dataclasses
import datetime
import os
from typing import List, Optional, Union

import requests


@dataclasses.dataclass(frozen=True)
class GatApiConfiguration:
    key: str
    root: str = "https://app.globalapptesting.com/api/"
    session: requests.Session = dataclasses.field(init=False, default_factory=requests.Session)
    version: str = dataclasses.field(default="v1", init=False)

    @property
    def uri(self) -> str:
        return os.path.join(self.root, self.version)

    def __post_init__(self):
        self.session.headers.update({"User-Agent": "gat.py", "X-Api-Key": self.key})


@dataclasses.dataclass(frozen=True)
class Organization:
    type: str = dataclasses.field(init=False, default="organization")
    id: str
    name: str


@dataclasses.dataclass(frozen=True)
class Application:
    type: str = dataclasses.field(init=False, default="application")
    id: str
    name: str
    platform_name: str


@dataclasses.dataclass(frozen=True)
class Environment:
    type: str = dataclasses.field(init=False, default="applicationEnvironment")
    id: str
    name: str
    url: str


@dataclasses.dataclass(frozen=True)
class NativeBuild:
    type: str = dataclasses.field(init=False, default="nativeApplicationBuild")
    id: str
    name: str
    original_file_name: str
    external_vendor_url: Optional[str]
    signing_status: Optional[str]


@dataclasses.dataclass(frozen=True)
class InternetBrowser:
    type: str = dataclasses.field(init=False, default="internetBrowser")
    id: str
    name: str
    operating_system_name: str


@dataclasses.dataclass(frozen=True)
class MobileDevice:
    type: str = dataclasses.field(init=False, default="mobileDevice")
    id: str
    name: str
    brand_name: str


@dataclasses.dataclass(frozen=True)
class TestCaseRunsBatchState:
    type: str = dataclasses.field(init=False, default="testCaseRunsBatchState")
    id: str
    state: str
    total_count: int
    in_progress_count: int
    completed_count: int
    failed_count: int
    passed_count: int
    cancelled_count: int


@dataclasses.dataclass(frozen=True)
class TestCaseRunsBatchTestCaseRun:
    type: str = dataclasses.field(init=False, default="testCaseRun")
    id: str
    name: str
    ada_url: str
    failed_results_count: int
    passed_results_count: int
    total_results_count: int


@dataclasses.dataclass(frozen=True)
class TestCaseRunsBatchSummary:
    type: str = dataclasses.field(init=False, default="testCaseRunsBatchSummary")
    id: str
    name: str
    start_time: Optional[datetime.datetime]
    finish_time: Optional[datetime.datetime]
    test_case_credits: int
    testers_involved: int
    application_id: str
    environment_id: str
    test_case_runs: List[TestCaseRunsBatchTestCaseRun]


@dataclasses.dataclass(frozen=True)
class TestCaseRunsBatch:
    type: str = dataclasses.field(init=False, default="testCaseRunsBatch")
    id: str


@dataclasses.dataclass(frozen=True)
class TestCaseInstruction:
    type: str = dataclasses.field(init=False, default="testCaseInstruction")
    id: str
    content: str
    assertion: bool


@dataclasses.dataclass(frozen=True)
class EmbeddedTestCase:
    type: str = dataclasses.field(init=False, default="testCase")
    id: str


@dataclasses.dataclass(frozen=True)
class TestCase:
    type: str = dataclasses.field(init=False, default="testCase")
    id: str
    title: str
    importance: Optional[str]
    section: Optional[str]
    instructions: List[Union[TestCaseInstruction, EmbeddedTestCase]]


@dataclasses.dataclass(frozen=True)
class Country:
    type: str = dataclasses.field(init=False, default="country")
    id: str
    name: str
    code: str
    available_platforms: List[str]


@dataclasses.dataclass(frozen=True)
class TestCaseRun:
    type: str = dataclasses.field(init=False, default="testCaseRun")
    id: str
    test_case_name: str
    test_case_section: str
    test_case_importance: str
    ada_url: str
    variations: List["TestCaseRun.Variation"]

    @dataclasses.dataclass(frozen=True)
    class Variation:
        name: str
        results: List["TestCaseRun.Variation.TestCaseRunResult"]

        @dataclasses.dataclass(frozen=True)
        class TestCaseRunResult:
            outcome: str
            attachment_url: str
            tester_comment: str
            steps_to_reproduce: List[str]
            reported_at: datetime.datetime
            country: str
