#!/bin/bash
set -ex

if [[ -n "$WITH_K8S" ]]; then
  # download kind
curl -Lo ./kind "https://kind.sigs.k8s.io/dl/v0.8.1/kind-$(uname)-amd64"
chmod +x ./kind

# create cluster
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

fi
