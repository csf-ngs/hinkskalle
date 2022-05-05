#!/usr/bin/env bash

set -x

mkdir -p conf/ results/
echo "POSTGRES_PASSWORD=supersecret" > conf/db_secrets.env
echo "HINKSKALLE_SECRET_KEY=superdupersecret" > conf/secrets.env
echo "DB_PASSWORD=supersecret" >> conf/secrets.env

set -eo pipefail
docker-compose -p conformance --project-directory ../../ config
docker-compose -p conformance --project-directory ../../ up -d
sleep 1
docker-compose -p conformance --project-directory ../../ exec -T api flask localdb add-user -u conform.hase -p conform -e conform@testha.se -f Conform -l Hase --admin
set +eo pipefail
echo "Starting tests..."
docker run --rm \
  --add-host=host.docker.internal:host-gateway \
  -v ${PROJECT_BASE:-$(pwd)}/results:/results \
  -w /results \
  -e OCI_ROOT_URL="http://${BACKEND_HOST:-host.docker.internal}:${BACKEND_PORT:-7660}" \
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
  ghcr.io/csf-ngs/oci-conformance

docker-compose -p conformance --project-directory ../../ logs api > ${PROJECT_BASE:-$(pwd)}/results/api.log
docker-compose -p conformance --project-directory ../../ down
