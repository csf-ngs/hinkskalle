import unittest

from Hinkskalle.models import Manifest, Tag

from Hinkskalle import db
from Hinkskalle.tests.model_base import ModelBase
from Hinkskalle.tests.models.test_Image import _create_image

class TestManifest(ModelBase):
  def test_manifest(self):
    image = _create_image()[0]

    manifest = Manifest(image_ref=image, content='blubb')
    db.session.add(manifest)
    db.session.commit()

    self.assertEqual(manifest.content, 'blubb')
    self.assertEqual(manifest.hash, 'fbea580d286bbbbb41314430d58ba887716a74d7134119c5307cdc9f0c7a4299')

    self.assertEqual(len(image.manifests_ref), 1)
  
  def test_manifest_json(self):
    image = _create_image()[0]
    manifest = Manifest(image_ref=image, content={'oi': 'nk'})
    db.session.add(manifest)
    db.session.commit()

    self.assertEqual(manifest.content, '{"oi": "nk"}')
    self.assertEqual(manifest.hash, '4fad2eb67a3846eefe75b6c40a0e0b727b16101db41713afa0f7039edcd0727c')