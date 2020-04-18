import asyncio
from unittest.mock import call

import pytest
from matrix_api_async import AsyncHTTPAPI
from matrix_client.errors import MatrixRequestError

from matrix import DatabaseMatrix
from opsdroid.cli.start import configure_lang
from opsdroid.connector.matrix import ConnectorMatrix
from opsdroid.core import OpsDroid


@pytest.fixture
def patched_send(mocker):
    return mocker.patch("matrix_api_async.api_asyncio.AsyncHTTPAPI._send")


@pytest.fixture
def opsdroid_matrix():
    connector = ConnectorMatrix(
        {
            "rooms": {"main": "#test:localhost"},
            "mxid": "@opsdroid:localhost",
            "password": "hello",
            "homeserver": "http://localhost:8008",
        }
    )
    connector.room_ids = {"main": "!notaroomid"}
    api = AsyncHTTPAPI("https://notaurl.com", None)
    connector.connection = api

    with OpsDroid() as opsdroid:
        opsdroid.connectors.append(connector)
        yield opsdroid


@pytest.mark.asyncio
async def test_default_config(patched_send, opsdroid_matrix):
    patched_send.return_value = {}

    db = DatabaseMatrix({}, opsdroid=opsdroid_matrix)
    await db.put("twim", {"hello": "world"})

    patched_send.assert_has_calls(
        [
            call("GET", "/rooms/%21notaroomid/state/opsdroid.database"),
            call(
                "PUT",
                "/rooms/%21notaroomid/state/opsdroid.database",
                {"twim": {"hello": "world"}},
                query_params={},
            ),
        ]
    )


@pytest.mark.asyncio
async def test_put_custom_state_key(patched_send, opsdroid_matrix):
    patched_send.return_value = {}

    db = DatabaseMatrix({"single_state_key": "wibble"}, opsdroid=opsdroid_matrix)
    await db.put("twim", {"hello": "world"})

    patched_send.assert_has_calls(
        [
            call("GET", "/rooms/%21notaroomid/state/opsdroid.database/wibble"),
            call(
                "PUT",
                "/rooms/%21notaroomid/state/opsdroid.database/wibble",
                {"twim": {"hello": "world"}},
                query_params={},
            ),
        ]
    )


@pytest.mark.asyncio
async def test_single_state_key_false(patched_send, opsdroid_matrix):
    patched_send.return_value = {}

    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    await db.put("twim", {"hello": "world"})

    patched_send.assert_has_calls(
        [
            call("GET", "/rooms/%21notaroomid/state/opsdroid.database/twim"),
            call(
                "PUT",
                "/rooms/%21notaroomid/state/opsdroid.database/twim",
                {"hello": "world"},
                query_params={},
            ),
        ]
    )


@pytest.mark.asyncio
async def test_single_state_not_a_dict(patched_send, opsdroid_matrix):
    patched_send.return_value = {}

    value = "world"
    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)
    await db.put("twim", value)

    patched_send.assert_has_calls(
        [
            call("GET", "/rooms/%21notaroomid/state/opsdroid.database"),
            call(
                "PUT",
                "/rooms/%21notaroomid/state/opsdroid.database",
                {"twim": value},
                query_params={},
            ),
        ]
    )


@pytest.mark.asyncio
async def test_default_not_a_dict(patched_send, opsdroid_matrix):
    patched_send.return_value = {}

    value = "world"
    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)

    with pytest.raises(ValueError):
        await db.put("twim", value)


@pytest.mark.asyncio
async def test_default_update_different_value(patched_send, opsdroid_matrix):
    patched_send.return_value = {"hello": "world"}

    value = {"red": "pill"}
    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)

    await db.put("twim", value)

    patched_send.assert_has_calls(
        [
            call("GET", "/rooms/%21notaroomid/state/opsdroid.database/twim"),
            call(
                "PUT",
                "/rooms/%21notaroomid/state/opsdroid.database/twim",
                {"hello": "world", "red": "pill"},
                query_params={},
            ),
        ]
    )


@pytest.mark.asyncio
async def test_default_update_same_key(patched_send, opsdroid_matrix):
    patched_send.return_value = {"hello": "world"}

    value = {"hello": "bob"}
    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)

    await db.put("twim", value)

    patched_send.assert_has_calls(
        [
            call("GET", "/rooms/%21notaroomid/state/opsdroid.database/twim"),
            call(
                "PUT",
                "/rooms/%21notaroomid/state/opsdroid.database/twim",
                value,
                query_params={},
            ),
        ]
    )


@pytest.mark.asyncio
async def test_update_same_key_single_state_key(patched_send, opsdroid_matrix):
    patched_send.return_value = {"twim": {"hello": "world"}}

    value = {"hello": "bob"}
    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)

    await db.put("twim", value)

    patched_send.assert_has_calls(
        [
            call("GET", "/rooms/%21notaroomid/state/opsdroid.database"),
            call(
                "PUT",
                "/rooms/%21notaroomid/state/opsdroid.database",
                {"twim": value},
                query_params={},
            ),
        ]
    )


@pytest.mark.asyncio
async def test_default_update_same_key_value(patched_send, opsdroid_matrix):
    patched_send.return_value = {"hello": "world"}

    value = {"hello": "world"}
    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)

    await db.put("twim", value)

    patched_send.assert_called_once_with("GET", "/rooms/%21notaroomid/state/opsdroid.database/twim")


@pytest.mark.asyncio
async def test_default_update_same_key_value_single_state_key(patched_send, opsdroid_matrix):
    patched_send.return_value = {"twim": {"hello": "world"}}

    value = {"hello": "world"}
    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)

    await db.put("twim", value)

    patched_send.assert_called_once_with("GET", "/rooms/%21notaroomid/state/opsdroid.database")


@pytest.mark.asyncio
async def test_default_update_single_state_key(patched_send, opsdroid_matrix):
    patched_send.return_value = {"twim": "hello"}

    value = {"pill": "red"}
    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)

    await db.put("pill", "red")


    patched_send.assert_has_calls(
        [
            call("GET", "/rooms/%21notaroomid/state/opsdroid.database"),
            call(
                "PUT",
                "/rooms/%21notaroomid/state/opsdroid.database",
                {"twim": "hello", "pill": "red"},
                query_params={},
            ),
        ]
    )


@pytest.mark.asyncio
async def test_get_single_state_key(patched_send, opsdroid_matrix):
    patched_send.return_value = {"twim": {"hello": "world"}}

    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)

    data = await db.get("twim")

    patched_send.assert_called_once_with("GET", "/rooms/%21notaroomid/state/opsdroid.database")

    assert data == {"hello": "world"}


@pytest.mark.asyncio
async def test_get(patched_send, opsdroid_matrix):
    patched_send.return_value = {"hello": "world"}

    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)

    data = await db.get("twim")

    patched_send.assert_called_once_with("GET", "/rooms/%21notaroomid/state/opsdroid.database/twim")

    assert data == {"hello": "world"}


@pytest.mark.asyncio
async def test_get_single_state_key(patched_send, opsdroid_matrix):
    patched_send.return_value = {"twim": "hello", "wibble": "wobble"}

    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)

    data = await db.get("twim")

    assert data == "hello"


@pytest.mark.asyncio
async def test_get_no_key_single_state_key(patched_send, opsdroid_matrix):
    patched_send.return_value = {"wibble": "wobble"}

    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)

    data = await db.get("twim")

    assert data is None


@pytest.mark.asyncio
async def test_get_no_key_404(patched_send, opsdroid_matrix):
    patched_send.side_effect = MatrixRequestError(code=404)

    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)

    data = await db.get("twim")

    assert data is None


@pytest.mark.asyncio
async def test_get_no_key_500(patched_send, opsdroid_matrix):
    patched_send.side_effect = MatrixRequestError(code=500)

    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)

    data = await db.get("twim")

    assert data is None


@pytest.mark.asyncio
async def test_connect(patched_send, opsdroid_matrix):
    db = DatabaseMatrix({}, opsdroid=opsdroid_matrix)

    await db.connect()
