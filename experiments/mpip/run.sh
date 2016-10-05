#!/bin/bash
#SBATCH --job-name=lulesh2.0+mpip
#SBATCH --nodes=8
#SBATCH --ntasks=16

SIZE=32
NTASKS=16
ITERATIONS=10

export SPACK_ROOT=/path/to/spack
source $SPACK_ROOT/share/spack/setup-env.sh
export PATH=$SPACK_ROOT/bin:$PATH

spack load mpi
spack load lulesh+mpip

mpirun -np $NTASKS lulesh2.0 -i $ITERATIONS -s $SIZE -p
