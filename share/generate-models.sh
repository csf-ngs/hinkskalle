#!/bin/bash

set -eo pipefail

curl http://localhost:7660/swagger |
  spotta -v DEBUG - typescript \
    -c Collection \
    -c Container \
    -c Entity \
    -c Image \
    -c Group \
    -c User \
    -c Group \
    -c GroupMember \
    -c Token \
    -c Job \
    -c LdapStatus \
    -c LdapPing \
    -c Manifest \
    -t backend/share/typescript-templates \
    -o frontend/src/store/models.ts
