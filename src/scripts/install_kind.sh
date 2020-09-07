#!/bin/bash
set -ex

if [[ -z $ENABLE_K8S_RUNNER_TESTS ]]; then
  exit 0
fi

# download kind
curl -Lo ./kind "https://kind.sigs.k8s.io/dl/v0.8.1/kind-$(uname)-amd64"
curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.18.0/bin/linux/amd64/kubectl

chmod +x ./kind
chmod +x ./kubectl

sudo mv ./kubectl /usr/local/bin/kubectl

# create cluster
kubectl version --client
./kind create cluster

cat <<EOF > pv.yaml
kind: PersistentVolume
apiVersion: v1
metadata:
  name: pv-hostpath
  labels:
    type: host
spec:
  persistentVolumeReclaimPolicy: Recycle
  storageClassName: manual
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteMany
  hostPath:
    path: "/tmp"
EOF

kubectl apply -f pv.yaml 
