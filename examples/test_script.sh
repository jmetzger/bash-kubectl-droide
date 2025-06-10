#!/bin/bash

# Example script for testing the MCP server
set -e

echo "=== Kubernetes Cluster Info ==="
kubectl cluster-info

echo -e "\n=== Available Nodes ==="
kubectl get nodes

echo -e "\n=== Current Namespace ==="
kubectl config current-context

echo -e "\n=== All Pods in default namespace ==="
kubectl get pods -n default

echo -e "\n=== All Services ==="
kubectl get services --all-namespaces

echo -e "\n=== Script completed successfully ==="