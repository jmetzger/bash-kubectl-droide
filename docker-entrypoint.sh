#!/bin/bash
set -e

# Decode base64 kubeconfig if KUBECONFIG_B64 is provided
if [ -n "$KUBECONFIG_B64" ]; then
    echo "Decoding base64 kubeconfig..."
    echo "$KUBECONFIG_B64" | base64 -d > /root/.kube/config
    chmod 600 /root/.kube/config
    export KUBECONFIG=/root/.kube/config
    echo "Kubeconfig successfully decoded and set"
    
    # Test kubectl connection
    echo "Testing kubectl connection..."
    kubectl version --client || echo "Warning: kubectl client version check failed"
else
    echo "Warning: KUBECONFIG_B64 environment variable not set"
fi

# Execute the original command
exec "$@"