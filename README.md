# 2IMW20 Path query size estimation
Path query size estimation project for the TU/e course 2IMW20 - Database Technology

This file gives all instructions necessary to get the project up and running and 
all command line options available.


## Development environment
In order to run the project in the same environment, you can use the docker container with
scientific python 2.7 on it which can be found here: https://hub.docker.com/r/dorxy/scientific-python-2.7-volume/
It's `/usr/local/` directory can be mounted to any local directory on your system so you can run your local 
code on the image.

## Installing dependencies
While the scientific python docker container comes with a lot of dependencies installed, any other dependencies
can be found in `requirements.txt` in the root of this repository. These requirements can be installed by executing:
```
pip install -r requirements.txt
```

## Commandline options
