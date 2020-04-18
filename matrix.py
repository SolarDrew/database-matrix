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
        self._state_key = config.get("state_key","opsdroid.database")
        _LOGGER.debug('Loaded matrix database connector')

    async def connect(self):
        """Connect to the database."""
        # Currently can't actually get connectors when this runs, so just store opsdroid instead
        _LOGGER.info(self.opsdroid)
        _LOGGER.info("Plugged into the matrix")

    async def put(self, key, value):
        """Insert or replace an object into the database for a given key."""
        room = self.room or 'main'
        room_id = room if room[0] == '!' else self.connector.room_ids[room]

        _LOGGER.debug(f"===== Putting {key} into matrix room {room_id}")

        ori_data = await self.get_state_event(room_id, key)
        data = {key: value}
        data = {**ori_data, **data}
        if data == ori_data:
            _LOGGER.debug("Not updating matrix state, as content hasn't changed.")
            return
        _LOGGER.debug(f"===== Putting {key} into matrix room {room_id} with {data}")

        await self.opsdroid.send(MatrixStateEvent(key=self._state_key,
                                                  content=data,
                                                  target=room_id,
                                                  connector=self.connector,
                                                  state_key=key))

    async def get(self, key):
        """Get a document from the database for a given key."""
        room = self.room or 'main'
        room_id = room if room.startswith('!') else self.connector.room_ids[room]

        _LOGGER.debug(f"Getting {key} from matrix room {room_id}")

        try:
            data = await self.get_state_event(room_id, key)
            data = data.get(key)
        except MatrixRequestError:
            data = None

        return data

    @property
    def connector(self):
        return self.opsdroid._connector_names['matrix']

    async def get_state_event(self, room_id, key):
        try:
            return await self.connector.connection._send("GET",
                                quote(f"/rooms/{room_id}/state/{self._state_key}/{key}"))
        except MatrixRequestError as e:
            if e.code != 404:
                raise e
            return {}
