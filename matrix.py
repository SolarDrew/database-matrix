import logging

from matrix_client.errors import MatrixRequestError
from opsdroid.database import Database


class DatabaseMatrix(Database):
    """A module for opsdroid to allow memory to persist in matrix room state."""

    def __init__(self, config):
        """Start the database connection."""
        self.name = "matrix"
        self.config = config
        self.room = 'main'
        logging.debug('Loaded matrix database connector')

    async def connect(self, opsdroid):
        """Connect to the database."""
        # Currently can't actually get connectors when this runs, so just store opsdroid instead
        self.opsdroid = opsdroid
        logging.info("Plugged into the matrix")

    async def put(self, key, data):
        """Insert or replace an object into the database for a given key."""
        logging.debug(f"Putting {key} into matrix")
        conn = self.connector
        room = self.room
        room_id = room if room[0] == '!' else conn.room_ids[room]

        await conn.connection.send_state_event(room_id,
                                               "opsdroid.database",
                                               data,
                                               state_key=key)

    async def get(self, key):
        """Get a document from the database for a given key."""
        logging.debug(f"Getting {key} from matrix")
        conn = self.connector
        room = self.room
        room_id = room if room[0] == '!' else conn.room_ids[room]

        try:
            data = await conn.connection._send("GET", f"/rooms/{room_id}/state/opsdroid.database/{key}")
        except MatrixRequestError:
            data = {}

        return data

    @property
    def connector(self):
        return self.opsdroid.default_connector
