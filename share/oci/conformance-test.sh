#!/usr/bin/env bash

docker run --rm \
  -v $(pwd)/results:/results \
  -w /results \
  -e OCI_ROOT_URL="http://172.28.128.1:7660" \
  -e OCI_NAMESPACE="myorg/myrepo" \
  -e OCI_USERNAME="myuser" \
  -e OCI_PASSWORD="mypass" \
  -e OCI_TEST_PULL=1 \
  -e OCI_TEST_PUSH=0 \
  -e OCI_TEST_CONTENT_DISCOVERY=1 \
  -e OCI_TEST_CONTENT_MANAGEMENT=1 \
  -e OCI_HIDE_SKIPPED_WORKFLOWS=0 \
  -e OCI_DEBUG=0 \
  -e OCI_DELETE_MANIFEST_BEFORE_BLOBS=1 \
  docker.ngs.vbcf.ac.at/oci-conformance 
