# Development environment

The following steps should be executed from within the folder `dev`.

To test popper, build the `popper-dev` image and prepare the folder to hold the venv
```
docker-compose build popper-dev
mkdir venv
```
then start the container and install deps into the venv
```
docker-compose run --rm popper-dev
# now you're insided the container
python -m virtualenv /venv
source /venv/bin/activate
pip install -e src/
```
From here on, you can always return to the container without having to re-install the venv.
However, don't forget to activate the venv after entering the container.
(The container is temporary and will be removed after you leave, so activate the venv each time.)
