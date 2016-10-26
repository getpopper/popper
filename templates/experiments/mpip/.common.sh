function find_or_install_spack {
  spack --version

  if [ $? -ne 0 ]; then
    echo "Couldn't find Spack. I'll install it now."
    mkdir -p $HOME/src/
    git clone https://github.com/llnl/spack $HOME/src/spack
    export SPACK_ROOT=$HOME/src/spack
  else
    export SPACK_ROOT=$(dirname `which spack`)
  fi

  source $SPACK_ROOT/share/spack/setup-env.sh
  export PATH=$SPACK_ROOT/bin:$PATH
}
