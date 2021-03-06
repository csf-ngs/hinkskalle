#!/usr/bin/env bash

docker-compose exec api flask localdb add-user -u conform.hase -p conform -e conform@testha.se -f Conform -l Hase --admin
docker run --rm \
  -v $(pwd)/results:/results \
  -w /results \
  -e OCI_ROOT_URL="http://172.28.128.1:7660" \
  -e OCI_NAMESPACE="myorg/myrepo" \
  -e OCI_USERNAME="conform.hase" \
  -e OCI_PASSWORD="conform" \
  -e OCI_TEST_PULL=1 \
  -e OCI_TEST_PUSH=1 \
  -e OCI_TEST_CONTENT_DISCOVERY=1 \
  -e OCI_TEST_CONTENT_MANAGEMENT=1 \
  -e OCI_HIDE_SKIPPED_WORKFLOWS=0 \
  -e OCI_DEBUG=0 \
  -e OCI_DELETE_MANIFEST_BEFORE_BLOBS=1 \
  docker.ngs.vbcf.ac.at/oci-conformance 

docker-compose exec api flask localdb remove-user conform.hase
