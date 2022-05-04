#!/usr/bin/env bash

mkdir -p conf/
echo "POSTGRES_PASSWORD=supersecret" > conf/db_secrets.env
echo "HINKSKALLE_SECRET_KEY=superdupersecret" > conf/secrets.env
echo "DB_PASSWORD=supersecret" >> conf/secrets.env

docker-compose --project-directory ../../ up -d
sleep 5
docker-compose --project-directory ../../ exec api flask localdb add-user -u conform.hase -p conform -e conform@testha.se -f Conform -l Hase --admin
echo "Starting tests..."
docker run --rm \
  --network host \
  -v $(pwd)/results:/results \
  -w /results \
  -e OCI_ROOT_URL="http://${BACKEND_HOST:-127.0.0.1}:${BACKEND_PORT:-17660}" \
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

docker-compose --project-directory ../../ exec api flask localdb remove-user conform.hase
docker-compose --project-directory ../../ logs api > results/api.log
docker-compose --project-directory ../../ down
