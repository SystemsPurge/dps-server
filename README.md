# DPS-SERVER
### HTTP api for dpsim for basic usage, no real time interface

# ENV

- `DPS_ROOT` : directory of files database
- `DPS_EXPORT` : continously export simulation results as prometheus metrics
- `DPS_MODE` : work with a local file database, or query a remote dps-server
- `DPS_LOG_LEVEL` : all the log levels supported by the python logging module
- `DPS_DEFAULTS` : path to default simulation parameters when using cli

defaults file must be a json file with all the default simulation parameter values,
that would not be explicitely passed to a cli command. Passed arguments will overwrite 
defaults.
# Usage

Run docker image `soullessblob/dps-server: alpha` or install requirements.txt ( in venv or otherwise )
, source the sv-env.sh script and run `uvicorn api-script:app --host 0.0.0.0 --port 5000`.
Source the client-env.sh to use the CLI to query the server. 
Make sure to change the paths in the scripts beforehand.
The fastapi documentation reflects the usage of the cli as well.
Simulation runs return no results, instead results need to be retrieved afterwards, e.g with the cli
`dps jtsget result <simname> -o <output path>` as json.

# CLI commands

1. `run` : Run a simulation
    #### Flags:
    - `-n` : Simulation (& result) name
    - `-f` : System Frequency
    - `-d` : Duration
    - `-t` : Timestep
    - `-opf` : Perform a pandapower optimal powerflow
    - `-dspf` : Perform a dpsim powerflow
    - `-pppf` : Perform a pandapower powerflow
    - `-up` : Use Profile data
    - `-ux` : Use XML files for system
    - `-dom` : Domain
    - `-s` : Solver
1. `tslist <tstype>` : list timeseries of a certain category
    #### Args:
    - `<tstype>` : timeseries type
3. `tsadd <tstype> <tspath>` : add a timeseries
    #### Args:
    - `<tstype>` : timeseries type
    - tspath: path to file
4. `tsdelete <tstype> <tsname>` : delete a timeseries
    #### Args:
    - `<tstype>` : timeseries type
    - `<tsname>`: keywords in file name
5. `xlist` : list xml
6. `xadd <xmlpath>` : add xml (based on the name of the folder/archive they were provided in)
    #### Args:
    - `<xmlpath>` : Path to xml (folder if local mode, otherwise an archive)
7. `xdelete <xmlname>` : delete xml
    #### Args:
    - `<tstype>` : keywords in file name
8. `jtsget <tstype> <tsname>` : get a timeseries in json
    #### Args:
    - `<tstype>` : timeseries type
    - `<tsname>` : keywords in file name
    #### Flags:
    - -o: Optional output file, otherwise prints to stdout