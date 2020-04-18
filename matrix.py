import logging
from urllib.parse import quote

from matrix_client.errors import MatrixRequestError
from opsdroid.database import Database
from opsdroid.connector.matrix.events import MatrixStateEvent

_LOGGER = logging.getLogger(__name__)


class DatabaseMatrix(Database):
    """A module for opsdroid to allow memory to persist in matrix room state."""

    def __init__(self, config, opsdroid=None):
        """Start the database connection."""
        super().__init__(config, opsdroid=opsdroid)
        self.name = "matrix"
        self.room = config.get("default_room", "main")
        self._event_type = "opsdroid.database"
        self._single_state_key = config.get("single_state_key", True)
        _LOGGER.debug("Loaded matrix database connector")

    async def connect(self):
        """Connect to the database."""
        _LOGGER.info("Matrix Database connector initialised.")

    async def put(self, key, value):
        """Insert or replace an object into the database for a given key."""

        # If the single state key flag is set then use that else use state key.
        state_key = "" if self._single_state_key is True else self._single_state_key or key

        room = self.room or "main"
        room_id = room if room[0] == "!" else self.connector.room_ids[room]

        _LOGGER.debug(f"Putting {key} into matrix room {room_id}.")

        ori_data = await self.get_state_event(room_id, state_key)

        if self._single_state_key:
            value = {key: value}

        elif not isinstance(value, dict):
            raise ValueError("When single_state_key is False value must be a dict.")

        data = {**ori_data, **value}

        if data == ori_data:
            _LOGGER.debug("Not updating matrix state, as content hasn't changed.")
            return

        _LOGGER.debug(f"===== Putting {key} into matrix room {room_id} with {data}")

        await self.opsdroid.send(
            MatrixStateEvent(
                key=self._event_type,
                content=data,
                target=room_id,
                connector=self.connector,
                state_key=state_key,
            )
        )

    async def get(self, key):
        """Get a document from the database for a given key."""
        room = self.room or "main"
        room_id = room if room.startswith("!") else self.connector.room_ids[room]

        _LOGGER.debug(f"Getting {key} from matrix room {room_id}")

        try:
            data = await self.get_state_event(room_id, key)
        except MatrixRequestError as e:
            _LOGGER.info(f"Failed to get state event with state_key={key}: {e}")
            data = None

        if not data:
            return

        if self._single_state_key:
            data = data.get(key)

        return data

    @property
    def connector(self):
        return self.opsdroid._connector_names["matrix"]

    async def get_state_event(self, room_id, key):

        url = f"/rooms/{room_id}/state/{self._event_type}"
        if key:
            url += f"/{key}"
        try:
            return await self.connector.connection._send("GET", quote(url))
        except MatrixRequestError as e:
            if e.code != 404:
                raise e
            return {}
