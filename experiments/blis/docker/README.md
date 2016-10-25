# docker-blis

[blis](https://github.com/flame/blis) in a container. The resulting 
image is used as [a use 
case](https://github.com/systemslab/popper/wiki/Popper-Math-Science) 
in reproducibility as part of [Popper](http://falsify.us).

The `entrypoint.sh` of the container runs the BLAS implementation 
comparison tests. BLAS alternate implementations are installed from 
Debian's package repositories 
([`atlas`](https://packages.debian.org/search?suite=all&section=all&arch=any&searchon=names&keywords=libatlas-base-dev) 
and 
[`openblas`](https://packages.debian.org/search?suite=all&section=all&arch=any&searchon=names&keywords=libopenblas-dev)). 
`blis` is installed from source and is compiled using the `reference` 
configuration.

To preserver output files from the tests, bind-mound the 
`/blis/test/output` folder. For example:

```
docker run --rm -v `pwd`/tests_output:/blis/test/output ivotron/blis
```
