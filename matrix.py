import logging

from matrix_client.errors import MatrixRequestError
from opsdroid.database import Database
from opsdroid.connector.matrix.events import MatrixStateEvent


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
        room = self.room
        room_id = room if room[0] == '!' else conn.room_ids[room]

        await self.opsdroid.send(MatrixStateEvent(key='opsdroid.database',
                                                  content={key: data},
                                                  target=room_id,
                                                  connector=self.connector))

    async def get(self, key):
        """Get a document from the database for a given key."""
        logging.debug(f"Getting {key} from matrix")
        room = self.room
        room_id = room if room[0] == '!' else conn.room_ids[room]

        try:
            data = await self.connector.get_state_event(room_id, f'opsdroid.database/{key}')
        except MatrixRequestError:
            data = {}

        return data

    @property
    def connector(self):
        return self.opsdroid._connector_names['matrix']
