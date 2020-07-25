#!/usr/bin/env sh

POPPER_VERSION="v2.7.0"

OS_NAME="$(uname)"
if [ "$OS_NAME" != "Linux" ] && [ "$OS_NAME" != "Darwin" ]; then
  echo "Popper only runs on Linux or MacOS. For Windows, we recommend WSL2."
  exit 1
fi

command -v docker >/dev/null 2>&1 || { echo >&2 "docker command not found. Aborting."; exit 1; }

cat > ./popper << "EOF"
#!/usr/bin/env sh

printenv > /tmp/.envfile

docker run --rm -ti \
  --volume /tmp:/tmp \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  --volume "$PWD":"$PWD" \
  --workdir "$PWD" \
  --env-file /tmp/.envfile \
  getpopper/popper:v2.7.0 $@
EOF

chmod +x "./popper"

echo
echo "Installed version $POPPER_VERSION to executable file '$PWD/popper'"
echo

while true; do
  read -p "Do you wish to move this binary to /usr/local/bin/? [Y/n] " yn < /dev/tty
  case $yn in
    [Yy]* ) echo "You might be asked for your (sudo) password."
      if [ -d "/usr/local/bin" ]; then
        sudo -p "password: " -- mv ./popper /usr/local/bin/
      else
        sudo -p "password: " -- mkdir -p /usr/local/bin/
        sudo mv ./popper /usr/local/bin/
      fi
      echo
      echo "Popper is now available for all users in this system!"
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
