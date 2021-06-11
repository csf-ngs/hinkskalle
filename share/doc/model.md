# Data Model

```mermaid
classDiagram
  Entity "1" --> "0..n" Collection
  Collection "1" --> "0..n" Container
  Container "1" --> "0..n" Image
  Container "1" --> "0..n" Tag
  Image "1" --> "0..n" Tag
  Image "1" --> "0..n" ImageUploadUrl
  File "0..1" --> "n" Image
  Manifest "0..1" --> "0..n" Tag
  Container "1" --> "0..n" Manifest
  ImageUploadUrl "1" --> "0..n" ImageUploadUrl : Chunks

  class Entity {
    +id: int
    +name: str
    +collections: Collection[]
  }
  class Collection {
    +id: int
    +name: str
    +containers: Container[]
  }
  class Container {
    +id: int
    +name: str
    +images: Image[]
  }
  class Image {
    +id: int
    +hash: sha256
    +location: path
    *tags: Tag[]
  }
  class Tag {
    +id: int
    +name: str
  }
  class Manifest {
    +id: int
    +hash: sha256
    +content: json
    *tags: Tag[]
  }
  class ImageUploadUrl {
    +id: uuid
  }
  class File {
    <<filesystem>>
    +path: path

  }
```