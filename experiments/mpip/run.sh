#!/bin/bash
#SBATCH --job-name=lulesh2.0+mpip
#SBATCH --nodes=8
#SBATCH --ntasks=16

source ./.common.sh
find_or_install_spack

SIZE=32
NTASKS=16
ITERATIONS=10

spack load openmpi@2.0.1
spack load lulesh@2.0.3+mpip

export MPIP="-t 10.0 -k 2 -f $PWD/results/"

mpirun -np $NTASKS lulesh2.0 -i $ITERATIONS -s $SIZE -p
