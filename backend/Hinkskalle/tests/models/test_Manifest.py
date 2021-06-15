from sqlalchemy.exc import IntegrityError

from Hinkskalle.models.Manifest import Manifest, ManifestContentSchema, ManifestSchema, ManifestTypes
from Hinkskalle.models.Tag import Tag

from Hinkskalle import db
from Hinkskalle.tests.model_base import ModelBase
from Hinkskalle.tests.models.test_Image import _create_image

class TestManifest(ModelBase):
  def test_manifest(self):
    image = _create_image()[0]
    tag = Tag(name='v1', image_ref=image, container_ref=image.container_ref)
    db.session.add(tag)
    db.session.commit()

    manifest = Manifest(content='blubb', container_ref=image.container_ref)
    tag.manifest_ref=manifest
    db.session.add(manifest)
    db.session.commit()

    self.assertEqual(manifest.content, 'blubb')
    self.assertEqual(manifest.hash, 'fbea580d286bbbbb41314430d58ba887716a74d7134119c5307cdc9f0c7a4299')

    self.assertIsNotNone(tag.manifest_ref)

    manifest2 = Manifest(content='blubb', container_ref=image.container_ref)
    tag.manifest_ref=manifest2
    db.session.add(manifest2)
    with self.assertRaises(IntegrityError):
      db.session.commit()
    
  def test_manifest_stale(self):
    image = _create_image()[0]
    tag = Tag(name='v1', image_ref=image, container_ref=image.container_ref)
    manifest = image.generate_manifest()
    tag.manifest_ref=manifest
    db.session.add(tag)

    self.assertFalse(manifest.stale)

    image.hash = 'sha256:somethingelse'
    self.assertTrue(manifest.stale)

  def test_manifest_stale_unreferenced(self):
    image = _create_image()[0]
    manifest = image.generate_manifest()

    self.assertFalse(manifest.stale)

    image.hash = 'sha256:somethingelse'
    self.assertTrue(manifest.stale)

  def test_manifest_json(self):
    image = _create_image()[0]

    manifest = Manifest(content={'oi': 'nk'}, container_ref=image.container_ref)
    db.session.add(manifest)
    db.session.commit()

    self.assertEqual(manifest.content, '{"oi": "nk"}')
    self.assertEqual(manifest.hash, '4fad2eb67a3846eefe75b6c40a0e0b727b16101db41713afa0f7039edcd0727c')
    self.assertDictEqual(manifest.content_json, {'oi': 'nk'})
  
  def test_manifest_content_schema(self):
    image = _create_image()[0]
    manifest = image.generate_manifest()

    content_load = ManifestContentSchema().load(manifest.content_json)
    self.assertDictEqual(content_load.errors, {})

  def test_manifest_schema(self):
    image = _create_image()[0]
    manifest = image.generate_manifest()

    dumped = ManifestSchema().dump(manifest)
    self.assertDictEqual(dumped.errors, {})
    self.assertListEqual(dumped.data['tags'], [])
    self.assertListEqual(dumped.data['images'], ['sha256:oink'])
    self.assertEquals(dumped.data['containerName'], image.container_ref.name)
    self.assertEquals(type(dumped.data['content']), dict)

    tag = Tag(name='v1', image_ref=image, manifest_ref=manifest)
    dumped = ManifestSchema().dump(manifest)
    self.assertListEqual(dumped.data['tags'], ['v1'])

  def test_manifest_type(self):
    image = _create_image()[0]
    manifest = Manifest(container_ref=image.container_ref, content={ 'some': 'thing' })
    self.assertEqual(manifest.type, ManifestTypes.invalid.name)

    manifest.content={
      'config': {
        'some': 'thing',
      }
    }
    self.assertEqual(manifest.type, ManifestTypes.invalid.name)

    manifest.content={
      'config': {
        'mediaType': 'something'
      }
    }
    self.assertEqual(manifest.type, ManifestTypes.other.name)

    manifest = image.generate_manifest()
    self.assertEqual(manifest.type, ManifestTypes.singularity.name)
  
  def test_manifest_total_size(self):
    image = _create_image()[0]
    manifest = Manifest(container_ref=image.container_ref)
    self.assertEqual(manifest.total_size, 0)

    manifest.content = {
      'layers': [
        {
          'mediaType': 'application/vnd.oci.image.layer.v1.tar+gzip', 
          'digest': 'sha256:1', 
          'size': 170, 
          'annotations': {'org.opencontainers.image.title': 'orasgrunz'}
        }
      ]
    }

    self.assertEqual(manifest.total_size, 170)

    manifest.content={
      'layers': [
        {
          'mediaType': 'application/vnd.oci.image.layer.v1.tar+gzip', 
          'digest': 'sha256:1', 
          'size': 170, 
          'annotations': { 'org.opencontainers.image.title': 'orasgrunz'}
        },
        {
          'mediaType': 'application/vnd.oci.image.layer.v1.tar+gzip', 
          'digest': 'sha256:2', 
          'size': 30, 
          'annotations': {'org.opencontainers.image.title': 'orasoink'}
        },
      ]
    }
    self.assertEqual(manifest.total_size, 200)

    manifest.content={
      'layers': [
        {
          'mediaType': 'application/vnd.oci.image.layer.v1.tar+gzip', 
          'digest': 'sha256:1', 
          'size': 170, 
          'annotations': { 'org.opencontainers.image.title': 'orasgrunz'}
        },
        {
          'mediaType': 'application/vnd.oci.image.layer.v1.tar+gzip', 
          'digest': 'sha256:2', 
          'annotations': {'org.opencontainers.image.title': 'orasoink'}
        },
      ]
    }
    self.assertEqual(manifest.total_size, 170)


  def test_manifest_filename(self):
    image = _create_image()[0]
    manifest = Manifest(container_ref=image.container_ref)
    self.assertEqual(manifest.filename, '(none)')

    manifest.content = {
      'layers': [
        {
          'mediaType': 'application/vnd.oci.image.layer.v1.tar+gzip', 
          'digest': 'sha256:1', 
          'size': 170, 
          'annotations': {'org.opencontainers.image.title': 'orasgrunz'}
        }
      ]
    }

    self.assertEqual(manifest.filename, 'orasgrunz')

    manifest.content={
      'layers': [
        {
          'mediaType': 'application/vnd.oci.image.layer.v1.tar+gzip', 
          'digest': 'sha256:1', 
          'size': 170, 
          'annotations': { 'org.opencontainers.image.title': 'orasgrunz'}
        },
        {
          'mediaType': 'application/vnd.oci.image.layer.v1.tar+gzip', 
          'digest': 'sha256:2', 
          'size': 30, 
          'annotations': {'org.opencontainers.image.title': 'orasoink'}
        },
      ]
    }
    self.assertEqual(manifest.filename, '(multiple)')

    manifest.content={
      'layers': [
        {
          'mediaType': 'application/vnd.oci.image.layer.v1.tar+gzip', 
          'digest': 'sha256:1', 
          'size': 170, 
          'annotations': { 'org.opencontainers.image.title': 'orasgrunz'}
        },
        {
          'mediaType': 'application/vnd.oci.image.layer.v1.tar+gzip', 
          'digest': 'sha256:2', 
          'size': 30, 
          'annotations': {}
        },
      ]
    }
    self.assertEqual(manifest.filename, 'orasgrunz')

    manifest.content={
      'layers': [
        {
          'mediaType': 'application/vnd.oci.image.layer.v1.tar+gzip', 
          'digest': 'sha256:1', 
          'size': 170, 
          'annotations': { 'org.opencontainers.image.title': 'orasgrunz'}
        },
        {
          'mediaType': 'application/vnd.oci.image.layer.v1.tar+gzip', 
          'digest': 'sha256:2', 
          'size': 30, 
        },
      ]
    }
    self.assertEqual(manifest.filename, 'orasgrunz')