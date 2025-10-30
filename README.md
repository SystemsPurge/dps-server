# DPS-SERVER
### HTTP api for dpsim for basic usage, no real time interface

# ENV

- `DPS_ROOT` : directory of files database
- `DPS_MODE` : work with a local file database, or query a remote dps-server
- `DPS_LOG_LEVEL` : all the log levels supported by the python logging module
- `DPS_DEFAULTS` : path to default simulation parameters when using cli

defaults file must be a json file with all the default simulation parameter values,
that would not be explicitely passed to a cli command. Passed arguments will overwrite 
defaults.
# Usage
Run docker image `registry.git.rwth-aachen.de/acs/public/dpsv:alpha0.1.0`:<br>
`docker run -p 5000:5000 registry.git.rwth-aachen.de/acs/public/dpsv:alpha0.1.0`<br
Then send your requests to localhost:5000.<br>
Optionally mount a db folder instead of using http, then use the container cli,
container mount path has to correspond to the DPS_ROOT variable.<br>
`docker run --name dpsv -v $(pwd)/db:/dpsroot registry.git.rwth-aachen.de/acs/public/dpsv:alpha0.1.0`.<br>
You can then put your needed files (xml,profiles) directly in the corresponding db subfolder,and use the cli:<br>
`docker exec dpsv sh -c 'dps run -ux <xml> -up <profile>...etc'`<br>
In this manner, results are retrieved from `<db folder>/result/<sim name>`.<br>
It is advised to explicitely alternate the usage of the server and the cli, there is no
resource coordination.<br>
CLI commands mirror the server HTTP API.

# CLI commands

1. `run` : Run a simulation
    #### Flags:
    - `-n` : Simulation (& result) name
    - `-f` : System Frequency
    - `-d` : Duration
    - `-t` : Timestep
    - `-opf` : Perform a pandapower optimal powerflow
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
    - `<xmlname>` : keywords in file name
8. `jtsget <tstype> <tsname>` : get a timeseries in json
    #### Args:
    - `<tstype>` : timeseries type
    - `<tsname>` : keywords in file name
    #### Flags:
    - -o: Optional output file, otherwise prints to stdout
