# Examples

In this section we present a examples of Popper pipelines. All these 
are available on github and can be added to a local repo by doing:

```bash
popper add popperized/<repo>/<pipeline>
```

Where `<repo>` is the name of the repository where a pipeline is 
contained, and `<pipeline>` is the name of the pipeline.

## Pipeline portability

  * [Using Virtualenv (Python)][pyv1] (and also [here][pyv2]).
  * [Using Packrat (R)][packrat].
  * [Using Spack][spack].
  * [Using Docker][docker].
  * [Using Vagrant][vagrant].

## Dataset Management

  * [Using Datapackages][datapackages].
  * [Using data.world][data-world].

## Infrastructure automation

  * [On CloudLab using geni-lib][cloudlab].
  * [On Chameleon using enos](chameleoncloud).
  * [On Google Compute Platform using terraform](gcp).

## Domain-specific pipelines

  * [Atmospheric science][nwp-wrf].
  * [Machine learning][docker].
  * [Linux kernel development][vagrant].
  * [Relational databases][postgres].
  * [Genomics][genomics].
  * [High Performance Computing][spack].
  * [Computational Neuroscience][sumatra].

Coming soon:

  * Distributed file systems
  * High energy physics
  * Applied Mathematical Science

## Results Validation

  * [Statistical validations][pyv2].
  * [Bitwise image comparison][docker].

## Pipeline Parametrization

  * [Using environment variables][envvar-parameters]
  * [Using baseliner][cloudlab].

## Provenance and automatic dependency resolution

  * [Using Sumatra][sumatra]

Coming soon:

  * Sci-Unit
  * ReproZip

[pyv1]: https://github.com/popperized/swc-lesson-pipelines/tree/master/pipelines/sea-surface-mapping
[pyv2]: https://github.com/popperized/popper-readthedocs-examples/tree/master/pipelines/validator
[spack]: https://github.com/popperized/popper-readthedocs-examples/tree/master/pipelines/mpip
[docker]: https://github.com/popperized/swc-lesson-pipelines/tree/master/pipelines/docker-data-science
[vagrant]: https://github.com/popperized/popper-readthedocs-examples/tree/master/pipelines/vagrant-linux
[sumatra]: https://github.com/popperized/open-comp-rsc-popper
[nwp-wrf]: https://github.com/popperized/nwp-popper
[genomics]: https://github.com/popperized/popper-readthedocs-examples/tree/master/pipelines/genomics
[datapackages]: https://github.com/popperized/popper-readthedocs-examples/tree/master/pipelines/datapackage
[postgres]: https://github.com/popperized/popper-readthedocs-examples/tree/master/pipelines/pgbench
[data-world]: https://github.com/popperized/popper-readthedocs-examples/tree/master/pipelines/data-world
[envvar-parameters]: https://github.com/popperized/popper-readthedocs-examples/tree/master/pipelines/envvar-param
[cloudlab]: https://github.com/popperized/popper-readthedocs-examples/tree/master/pipelines/cloudlab-benchmarking
[chameleoncloud]: https://github.com/popperized/popper-readthedocs-examples/tree/master/pipelines/chameleon-benchmarking
[gcp]: https://github.com/popperized/popper-readthedocs-examples/tree/master/pipelines/gce-benchmarking
[packrat]: https://github.com/popperized/popper-readthedocs-examples/tree/master/pipelines/sea-surface-mapping-r
