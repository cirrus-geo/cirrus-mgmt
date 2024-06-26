import json
import os
import shlex
import shutil
from pathlib import Path
from unittest.mock import patch

import boto3
import botocore
import moto
import pytest
from cirrus.cli.commands import cli
from click.testing import CliRunner

try:
    # temporary measure while waiting on pending PRs
    from cirrus.lib2.eventdb import EventDB
except ImportError:
    EventDB = None

from cirrus.core.project import Project
from cirrus.lib2.process_payload import ProcessPayload, ProcessPayloads
from cirrus.lib2.statedb import StateDB


def set_fake_creds():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["AWS_REGION"] = "us-east-1"


set_fake_creds()


@pytest.fixture(autouse=True)
def aws_credentials():
    set_fake_creds()


@pytest.fixture(scope="session")
def fixtures():
    return Path(__file__).parent.joinpath("fixtures")


@pytest.fixture(scope="session")
def statedb_schema(fixtures):
    return json.loads(fixtures.joinpath("statedb-schema.json").read_text())


@pytest.fixture(scope="module")
def project_testdir():
    pdir = Path(__file__).parent.joinpath("output")
    if pdir.is_dir():
        shutil.rmtree(pdir)
    pdir.mkdir()
    Project.new(pdir)
    old_cwd = os.getcwd()
    os.chdir(pdir)
    yield pdir
    os.chdir(old_cwd)


@pytest.fixture
def project(project_testdir):
    return Project.resolve(strict=True)


@pytest.fixture
def s3(aws_credentials):
    with moto.mock_s3():
        yield boto3.client("s3", region_name="us-east-1")


@pytest.fixture
def sqs(aws_credentials):
    with moto.mock_sqs():
        yield boto3.client("sqs", region_name="us-east-1")


@pytest.fixture
def dynamo():
    with moto.mock_dynamodb():
        yield boto3.client("dynamodb", region_name="us-east-1")


@pytest.fixture
def stepfunctions(aws_credentials):
    with moto.mock_stepfunctions():
        yield boto3.client("stepfunctions", region_name="us-east-1")


@pytest.fixture
def iam(aws_credentials):
    with moto.mock_iam():
        yield boto3.client("iam", region_name="us-east-1")


@pytest.fixture(autouse=True)
def sts(aws_credentials):
    with moto.mock_sts():
        yield


@pytest.fixture
def payloads(s3):
    name = "payloads"
    s3.create_bucket(Bucket=name)
    return name


@pytest.fixture
def data(s3):
    name = "data"
    s3.create_bucket(Bucket=name)
    return name


@pytest.fixture
def queue(sqs):
    q = sqs.create_queue(QueueName="test-queue")
    q["Arn"] = "arn:aws:sqs:us-east-1:123456789012:test-queue"
    return q


@pytest.fixture
def timestream_write_client():
    with moto.mock_timestreamwrite():
        yield boto3.client("timestream-write", region_name="us-east-1")


if EventDB:

    @pytest.fixture
    def eventdb(timestream_write_client):
        timestream_write_client.create_database(DatabaseName="event-db-1")
        timestream_write_client.create_table(
            DatabaseName="event-db-1", TableName="event-table-1"
        )
        return EventDB("event-db-1|event-table-1")


@pytest.fixture
def statedb(dynamo, statedb_schema, eventdb=None) -> str:
    dynamo.create_table(**statedb_schema)
    table_name = statedb_schema["TableName"]
    if eventdb:
        return StateDB(table_name=table_name, eventdb=eventdb)
    else:
        return StateDB(table_name=table_name)


@pytest.fixture
def workflow(stepfunctions, iam):
    defn = {
        "StartAt": "FirstState",
        "States": {
            "FirstState": {
                "Type": "Pass",
                "End": True,
            },
        },
    }
    role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "states.us-east-1.amazonaws.com",
                },
                "Action": "sts:AssumeRole",
            }
        ],
    }
    role = iam.create_role(
        RoleName="test-step-function-role",
        AssumeRolePolicyDocument=json.dumps(role_policy),
    )["Role"]
    return stepfunctions.create_state_machine(
        name="test-workflow1",
        definition=json.dumps(defn),
        roleArn=role["Arn"],
    )


# moto does not mock lambda GetFunctionConfiguration
# see https://docs.getmoto.org/en/latest/docs/services/patching_other_services.html
orig = botocore.client.BaseClient._make_api_call

LAMBDA_ENV_VARS = {"var": "value"}


@pytest.fixture
def lambda_env():
    return LAMBDA_ENV_VARS


def mock_make_api_call(self, operation_name, kwarg):
    if operation_name == "GetFunctionConfiguration":
        return {"Environment": {"Variables": LAMBDA_ENV_VARS}}
    return orig(self, operation_name, kwarg)


@pytest.fixture
def mock_lambda_get_conf():
    with patch(
        "botocore.client.BaseClient._make_api_call",
        new=mock_make_api_call,
    ):
        yield


@pytest.fixture(scope="session")
def cli_runner():
    return CliRunner(mix_stderr=False)


@pytest.fixture(scope="session")
def invoke(cli_runner):
    def _invoke(cmd, **kwargs):
        kwargs["catch_exceptions"] = kwargs.get("catch_exceptions", False)
        return cli_runner.invoke(cli, shlex.split(cmd), **kwargs)

    return _invoke


@pytest.fixture
def basic_payloads(fixtures, statedb):
    payload_list = [
        ProcessPayload(json.loads(fixtures.joinpath("basic_payload.json").read_text()))
    ]
    try:
        # cirrus-geo >= 0.15.0
        payloads = ProcessPayloads(process_payloads=payload_list, statedb=statedb)
    except TypeError as te:
        # cirrus-geo < 0.15.0
        if "unexpected keyword argument 'statedb'" in te.args[0]:
            payloads = ProcessPayloads(process_payloads=payload_list)
        else:
            raise
    return payloads
