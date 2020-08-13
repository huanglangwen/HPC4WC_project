# A Python Implementation of GFS Scale-Aware Mass-Flux Shallow Convection Scheme Module
## Package `shalconv` structure
- `__init__.py`: configuration
- `funcphys.py`: thermodynamic functions
- `physcons.py`: Constants
- `samfaerosols.py`: Aerosol process
- `samfshalcnv.py`: shalcnv scheme
- `serialization.py`: Serialization
- `kernels/stencils_*.py`: GT4Py stencils of the shalcnv scheme
- `kernels/utils.py`: useful functions for GT4Py arrays

## Unit tests
- `analyse_xml.py`: dependency analysis of fortran code
- `read_serialization.py`: read serialization data for unit tests
- `run_serialization.py`: generate serialization for unit tests
- `test_fpvsx.py`: test fpvsx function
- `test_part1.py`: test part1 of shalconv scheme
- `test_part2.py`: test part2 of shalconv scheme
- `test-part34.py`: test part3 and part4 of shalconv scheme

## Other files
- `build.sh`: script for building environment as docker image
- `enter.sh`: script for entering the docker environment
- `env_daint`: script for setting up environment in Piz Daint
- `submit_job.sh`: script for submitting SLURM jobs in Piz Daint of benchmarking shalconv scheme with gtcuda and gtx86 backends
- `main.py`: validation for shalconv scheme
- `benchmark.py`: benchmark shalconv scheme with various number of columns (ix)
- `plot.py`: plot benchmark results (already hardcoded)

## Storage in GT4Py
All the arrays are broadcasted or sliced to the shape (1, ix, km) due to restrictions of gt4py stencil.
Operations applied to 1D array of shape (1, ix, 1) are propagated forward and then backward to keep consistency.

## Configuration
`shalconv/__init__.py` specifies several configurations needed to run the scheme, including location of serialization data, backend type,
verbose output and floating/integer number type. One can also specify backend type by setting the environment variable `GT4PY_BACKEND` to be
one of `numpy`, `debug`, `gtx86`, `gtcuda`.

## Build with docker in Linux
execute `build.sh` then `enter.sh`.

## Build with docker in Windows
1. execute `docker build -t hpc4wc_project .`
2. execute `docker run -i -t --rm --mount type=bind,source={ABSOLUTE PATH OF THIS FOLDER},target=/work --name=hpc4wc_project hpc4wc_project`
3. execute `ipython main.py` or `benchmark.py`

## Run on Piz Diant
1. CHANGE `ISDOCKER` to False and `DATAPATH` in `shalconv/__init__.py`
2. execute `source env_diant`
3. execute `ipython main.py` or `benchmark.py`

## Tests
Inside tests folder, execute `ipython run_serialization.py` to generate serialization
data needed for tests, then execute `ipython test_*.py` to run tests.
