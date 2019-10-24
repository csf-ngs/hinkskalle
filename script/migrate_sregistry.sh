#!/bin/bash

cd /groups/vbcf-ngs/misc/infra/sregistry/pipeline

ls | grep -v latest | while read img; do
  IFS=$'\uf022'
  read -ra IMG <<< "$img"
  tag=${IMG[1]%@*}
  singularity push -U "$img" library://default/pipeline/${IMG[0]}:$tag
done

