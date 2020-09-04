#!/usr/bin/env sh

# Move the "popper" executable to /usr/local/bin/.
install_system_wide() {
  if command -v sudo >/dev/null 2>&1; then
    echo "You might be asked for your (sudo) password."
    if [ -d "/usr/local/bin" ]; then
      sudo -p "password: " -- mv ./popper /usr/local/bin/
    else
      sudo -p "password: " -- mkdir -p /usr/local/bin/
      sudo mv ./popper /usr/local/bin/
    fi
  else
    echo
    echo "sudo command not found. Trying to move file without sudo..."
    if ! mkdir -p /usr/local/bin/ || ! mv ./popper /usr/local/bin/; then
      echo >&2
      echo >&2 "Moving popper to /usr/local/bin failed."
      echo >&2 "Try executing this script as root user."
      exit 1
    fi
  fi
  echo
  echo "Popper is now available for all users in this system!"
}

POPPER_VERSION="v2020.09.1"

OS_NAME="$(uname)"
if [ "$OS_NAME" != "Linux" ] && [ "$OS_NAME" != "Darwin" ]; then
  echo "Popper only runs on Linux or MacOS. For Windows, we recommend WSL2."
  exit 1
fi

command -v docker >/dev/null 2>&1 || { echo >&2 "docker command not found. Aborting."; exit 1; }

# We override the environment variables PATH of the host system with the
# default of Popper’s Docker image. This prevents unforeseeable side effects if
# the host’s PATH is non-standard.
cat > ./popper << "EOF"
#!/usr/bin/env sh

printenv > /tmp/.envfile

docker run --rm -ti \
  --volume /tmp:/tmp \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  --volume "$PWD":"$PWD" \
  --workdir "$PWD" \
  --env-file /tmp/.envfile \
  --env "PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
  getpopper/popper:v2020.09.1 "$@"
EOF

if [ "$?" -eq 0 ]; then
  echo
  echo "Installed version $POPPER_VERSION to executable file '$PWD/popper'"
  echo
else
  echo >&2
  echo >&2 "Creating 'popper' file failed."
  echo >&2 "Please make sure you have write permission in this folder and try again."
  exit 1
fi

chmod +x "./popper"

while true; do
  read -p "Do you wish to move this binary to /usr/local/bin/? [Y/n] " yn < /dev/tty
  case $yn in
    [Yy]* )
      install_system_wide
      break
      ;;
    [Nn]* ) echo
      echo "To make the popper command globally available, add it"
      echo "to a folder reachable by the PATH variable."
      echo
      break
      ;;
    * ) echo
      echo "Please answer 'Y' or 'n'."
      echo
      ;;
  esac
done
