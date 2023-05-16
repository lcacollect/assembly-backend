import json

import pytest
from pytest_httpx import HTTPXMock

from import_data.ecoplatform import ECOPLATFORM_URL
from import_data.okobau import OKOBAU_URL


@pytest.fixture()
def ecoplatform_token() -> str:
    yield "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJjaHJrIiwiaXNzIjoiRUNPUE9SVEFMIiwiYXVkIjoiYW55IiwidmVyIjoiNy4yLjEiLCJwZXJtaXNzaW9ucyI6WyJ1c2VyOnJlYWQsd3JpdGU6MTE4Iiwic3RvY2s6cmVhZCxleHBvcnQ6MiIsInN0b2NrOnJlYWQsZXhwb3J0OjEiXSwicm9sZXMiOltdLCJpYXQiOjE2NTcwMjIxMzMsImV4cCI6MTY2NDkwNjEzMywiZW1haWwiOiJjaHJrQGFya2l0ZW1hLmNvbSIsInRpdGxlIjoiIiwiZmlyc3ROYW1lIjoiQ2hyaXN0aWFuIiwibGFzdE5hbWUiOiJLb25nc2dhYXJkIiwiZ2VuZXJhdGVOZXdUb2tlbnMiOmZhbHNlLCJqb2JQb3NpdGlvbiI6IiIsImFkZHJlc3MiOnsiY2l0eSI6IiIsInppcENvZGUiOiIiLCJjb3VudHJ5IjoiREsiLCJzdHJlZXQiOiIifSwib3JnYW5pemF0aW9uIjp7fSwidXNlckdyb3VwcyI6W3sidXNlckdyb3VwTmFtZSI6InJlZ2lzdGVyZWRfdXNlcnMiLCJ1c2VyR3JvdXBPcmdhbml6YXRpb25OYW1lIjoiRGVmYXVsdCBPcmdhbml6YXRpb24ifV0sImFkbWluaXN0cmF0ZWRPcmdhbml6YXRpb25zTmFtZXMiOiIiLCJwaG9uZSI6IiIsImRzcHVycG9zZSI6IlJlYWQgRVBEIGRhdGEiLCJzZWN0b3IiOiIiLCJpbnN0aXR1dGlvbiI6IkFya2l0ZW1hIn0.1HfmC9qLvJojVTojAjt9Wq9QjHW3ZoFH_4u3GU-Gg-LgOxc4Ths_EiOT9g4bpjB0VMTrVwUIlE5lJWGZepoE2_PGybBS2XV4-StrlpAqB9dCPt-z6qHnCeHnJXyh_VL6IvHc6PSFyX_onCoEu91pAZ2jEjNvsjVOFzvFOqBUiA8"


@pytest.fixture()
def mock_oko_get_number_of_epds(datafix_dir, httpx_mock: HTTPXMock) -> dict:
    name = "oko_url_processes_countonly"
    mock_data = json.loads((datafix_dir / f"{name}.json").read_text())
    httpx_mock.add_response(url=f"{OKOBAU_URL}/processes?countOnly=true&format=json", json=mock_data)

    return mock_data


@pytest.fixture()
def mock_oko_get_epd_ids(datafix_dir, httpx_mock: HTTPXMock) -> dict:
    name = "oko_url_processes_pagesize"
    mock_data = json.loads((datafix_dir / f"{name}.json").read_text())
    httpx_mock.add_response(url=f"{OKOBAU_URL}/processes?format=json&pageSize={1}", json=mock_data)

    return mock_data


@pytest.fixture()
def okobau_epd_url() -> str:
    uid = "f63ac879-fa7d-4f91-813e-e816cbdf1927"
    version = "00.00.025"
    yield f"{OKOBAU_URL}/processes/{uid}?version={version}"


@pytest.fixture()
def mock_oko_get_epd_data(datafix_dir, httpx_mock: HTTPXMock, okobau_epd_url) -> dict:
    uid = "f63ac879-fa7d-4f91-813e-e816cbdf1927"
    mock_data = json.loads((datafix_dir / f"{uid}.json").read_text())
    httpx_mock.add_response(url=f"{okobau_epd_url}&format=json", json=mock_data)

    return mock_data


@pytest.fixture()
def mock_oko_get_flow_dataset_4e1beb5b(datafix_dir, httpx_mock: HTTPXMock) -> dict:
    uid = "4e1beb5b-f059-4aa9-b12a-4462eb1fa606"
    mock_data = json.loads((datafix_dir / f"{uid}.json").read_text())
    httpx_mock.add_response(url=f"{OKOBAU_URL}/flows/{uid}?version=00.00.004&format=json", json=mock_data)

    return mock_data


@pytest.fixture()
def mock_oko_get_flow_dataset_8fc69490(datafix_dir, httpx_mock: HTTPXMock) -> dict:
    uid = "8fc69490-4aad-c4a4-9ecb-c9e76c97038e"
    mock_data = json.loads((datafix_dir / f"{uid}.json").read_text())
    httpx_mock.add_response(url=f"{OKOBAU_URL}/flows/{uid}?format=json", json=mock_data)

    return mock_data


@pytest.fixture()
def mock_eco_get_flow_dataset(datafix_dir, httpx_mock: HTTPXMock) -> dict:
    uid = "46bc366c-f6c2-4848-86d3-13be27107903"
    mock_data = json.loads((datafix_dir / f"{uid}.json").read_text())
    httpx_mock.add_response(
        url=f"https://epdireland.lca-data.com/resource/flows/{uid}?version=00.01.000&format=json",
        json=mock_data,
    )

    return mock_data


@pytest.fixture()
def mock_eco_get_epd_ids(datafix_dir, httpx_mock: HTTPXMock) -> dict:
    name = "eco_url_processes_pagesize"
    mock_data = json.loads((datafix_dir / f"{name}.json").read_text())
    url = f"{ECOPLATFORM_URL}/processes?search=true&distributed=true&virtual=true&metaDataOnly=false&format=json&startIndex={0}&pageSize={1}"
    httpx_mock.add_response(url=url, json=mock_data)

    return mock_data


@pytest.fixture()
def ecoplatform_epd_url() -> str:
    yield "https://epdireland.lca-data.com/resource/processes/f256594a-a7bf-4bbb-91d0-65be256377c0?version=00.03.000"


@pytest.fixture()
def mock_eco_get_epd_data(datafix_dir, httpx_mock: HTTPXMock, ecoplatform_epd_url) -> dict:
    uid = "f256594a-a7bf-4bbb-91d0-65be256377c0"
    mock_data = json.loads((datafix_dir / f"{uid}.json").read_text())
    httpx_mock.add_response(url=f"{ecoplatform_epd_url}&format=json", json=mock_data)

    return mock_data
