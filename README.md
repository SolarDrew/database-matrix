# opsdroid database matrix

A database module for opsdroid to persist memory in matrix room state.

## Requirements

To use this database the opsdroid instance needs to use a matrix connector.

## Configuration

```
connectors:
  matrix # see connector-matrix configuration
  
databases:
  matrix:
    default_room: 'main'
    single_state_key: 'opsdroid.database'
```
