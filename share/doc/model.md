# Data Model

```mermaid
classDiagram
  Entity "1" --> "n" Collection
  Collection "1" --> "n" Container
  Container "1" --> "n" Image
  Image "1" --> "n" Tag
  Image "1" --> "n" ImageUploadUrl
  File "1" --> "n" Image
  ImageUploadUrl "1" --> "n" ImageUploadUrl
  Manifest "1" --> "n" Tag

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
  }
  class Tag {
    +id: int
    +name: str
  }
  class Manifest {
    +id: int
    +hash: sha256
    +content: json
  }
  class ImageUploadUrl {
    +id: uuid
  }
  class File {
    <<filesystem>>
    +path: path

  }
```