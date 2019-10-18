# Reverse Engineering

Patch singularity with `share/singularity-plain-http.patch` for testing


Mostly from:

[https://github.com/sylabs/scs-library-client.git](https://github.com/sylabs/scs-library-client.git)

- `client/response.go` has JSON defs
- `client/models.go` defines entity, collection, container, image, ...

NB: JSON keys case insensitive? seem to mostly post lower case, but also with uppercased first letter (see below)

Less:

[https://github.com/sylabs/singularity.git](https://github.com/sylabs/singularity.git)

- `internal/pkg/remote/remote.go` service setup (config), auth


## Required Routes

- `GET /version`

has to return some kind of version information. Does not seem to matter much:

```
{
  "version": "2.0.0",
  "apiVersion": "2.0.0",
}
```

This could be used to pick the upload path (one-step in v1, three steps in v2) as well as tag format (v2+ has architecture dependend tags, which seems to be unused)

- `GET /assets/config/config.prod.json`

return service endpoint configuration. required services:

```
{
  "libraryAPI": {
    "uri": "http://172.28.128.1:7660"
  },
  "keystoreAPI": {
    "uri": "http://172.28.128.1:7660"
  },
  "tokenAPI": {
    "uri": "http://172.28.128.1:7660"
  }
}
```

keystore is not implemented, but avoids warning on push when specified

- `GET /v1/token-status`

receives `Authorization: Bearer [token]`. Return 200 OK when valid, content wurscht.

- `GET /v1/entities/<string:name>`
- `POST /v1/entities` 
- `GET /v1/collections/<string:entity>/<string:collection>`
- `POST /v1/collections`
- `GET /v1/containers/<string:entity>/<string:collection>/<string:container>`
- `POST /v1/containers`
- `GET /v1/tags/<string:container>`
- `POST /v1/tags/<string:container>`
- `GET /v1/images/<path:image_ref>` (image\_ref: /entity?/collection/container:tag); tag can also be a sha256 hash (`sha256.5056...`) on push (checks if image exists?)
- `POST /v1/images`
- `GET /v1/imagefile/<path:image_ref>` download actual file
- `POST /v1/imagefile//<string:image_id>` upload file (*raw body*)
- `GET /v1/search?value=[search]`

json response struct except for config.prod.json:

```
{ "data": <obj>, "error?": ?? }
```

search returns lists of `entity`, `collection`, `container`; `image` ignored?

## Pull Procedure

1. get image
2. get imagefile
3. compare hash from image metadata to imagefile

## Push Procedure

1. get or create entity
2. get or create collection
3. get or create container
4. get or create image
5. upload/post imagefile
6. set tags (add/update existing tags with image id) (not latest)

## Models

base props not so interesting, maybe `deleted` (soft delete marker)

Entity:

- id
- name
- description
- collections[]

Collection:

- id
- name
- description
- entityName
- entity (id)
- containers[]

Container:

- id
- name
- description
- imageTags
- archTags (v2)
- size? (-> number of images??)
- private?
- readOnly?
- collection (id)
- collectionName
- entity (id)
- entityName
- images[]

Image:

- id
- hash (`sha256.[hash]`)
- description
- blob??
- size?
- uploaded t/f
- container (id)
- containerName
- entity (id)
- entityName
- collection (id)
- collectionName
- tags (string list, one image can have many tags)


Entity -> has many -> Collection -> has many -> Container -> has many -> Images

Container -> has many -> Tag -> has one -> Image
