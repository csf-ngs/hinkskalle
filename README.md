# Hinkskalle

(buckethead)

Partial implementation of the Sylab's singularity library protocol [https://cloud.sylabs.io/library](https://cloud.sylabs.io/library)

Should be able to do:

- `singularity pull library://user/collection/image:tag`
- `singularity push -U image.sif library://user/collection/image:tag`
- `singularity search resi # where is my cow?`

Auxiliary:

- `singularity remote add testhase https://singularity.ngs.vbcf.ac.at/`
- `singularity remote use testhase`
- `singularity remote login` 

Login (token) is necessary for pushing images.
