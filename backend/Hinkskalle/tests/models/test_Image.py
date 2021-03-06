from typing import Tuple
import unittest
from unittest import mock
from datetime import datetime, timedelta
import os.path
from shutil import which, rmtree
import subprocess

from Hinkskalle.models.Entity import Entity
from Hinkskalle.models.Collection import Collection
from Hinkskalle.models.Container import Container
from Hinkskalle.models.Image import Image, ImageSchema
from Hinkskalle.models.Tag import Tag

from Hinkskalle.tests.models.test_Collection import _create_collection

from Hinkskalle import db
from ..model_base import ModelBase
from .._util import _create_user, _create_image

class TestImage(ModelBase):

  def test_image(self):
    entity = Entity(name='test-hase')
    db.session.add(entity)
    db.session.commit()

    coll = Collection(name='test-collection', entity_ref=entity)
    db.session.add(coll)
    db.session.commit()

    container = Container(name='test-container',collection_ref=coll)
    db.session.add(container)
    db.session.commit()

    image = Image(description='test-image', container_ref=container)
    db.session.add(image)
    db.session.commit()

    read_image = Image.query.get(image.id)
    self.assertTrue(abs(read_image.createdAt - datetime.now()) < timedelta(seconds=1))

    self.assertEqual(read_image.container(), container.id)
    self.assertEqual(read_image.containerName(), container.name)

    self.assertEqual(read_image.collection(), coll.id)
    self.assertEqual(read_image.collectionName(), coll.name)

    self.assertEqual(read_image.entity(), entity.id)
    self.assertEqual(read_image.entityName(), entity.name)
  
  def test_manifest(self):
    image = _create_image(media_type='application/vnd.sylabs.sif.layer.v1.sif')[0]
    image.size = 666

    manifest = image.generate_manifest()

    self.assertRegex(manifest.content, r'"schemaVersion": 2')
    self.assertRegex(manifest.content, rf'"digest": "sha256:{image.hash.replace("sha256.", "")}"')
    self.assertRegex(manifest.content, rf'"org.opencontainers.image.title": "{image.container_ref.name}"')
    self.assertRegex(manifest.content, rf'"size": {image.size}')

  def test_manifest_mediatype(self):
    image = _create_image(media_type='application/vnd.docker.image.rootfs.diff.tar.gzip')[0]
    image.size = 666
    db.session.commit()

    with self.assertRaises(Exception):
      image.generate_manifest()


  def test_tags(self):
    image = _create_image()[0]

    tag1 = Tag(name='v1', image_ref=image)
    db.session.add(tag1)
    db.session.commit()
    tag2 = Tag(name='v2', image_ref=image)
    db.session.add(tag2)
    db.session.commit()

    self.assertListEqual(image.tags(), ['v1', 'v2'])
    Tag.__table__.delete()
  
  def test_tags_case(self):
    image = _create_image()[0]
    tag1 = Tag(name='TestHase', image_ref=image)
    db.session.add(tag1)
    db.session.commit()
    self.assertListEqual(image.tags(), ['testhase'])
  
  def test_access(self):
    admin = _create_user(name='admin.oink', is_admin=True)
    user = _create_user(name='user.oink', is_admin=False)
    image = _create_image()[0]
    self.assertTrue(image.check_access(admin))
    self.assertTrue(image.check_access(user))
    self.assertTrue(image.check_access(None))
  
  def test_access_private(self):
    admin = _create_user(name='admin.oink', is_admin=True)
    user = _create_user(name='user.oink', is_admin=False)

    image, container, _, _ = _create_image()
    container.private = True

    self.assertFalse(image.check_access(None))
    self.assertTrue(image.check_access(admin))
    self.assertFalse(image.check_access(user))

    container.owner = user
    self.assertTrue(image.check_access(user))

  
  def test_update_access(self):
    admin = _create_user(name='admin.oink', is_admin=True)
    user = _create_user(name='user.oink', is_admin=False)

    image, container, _, _ = _create_image()
    self.assertTrue(image.check_update_access(admin))
    self.assertFalse(image.check_update_access(user))

    container.owner = user
    self.assertTrue(image.check_update_access(user))


  def test_schema(self):
    schema = ImageSchema()

    image = _create_image()[0]

    serialized = schema.dump(image)
    self.assertEqual(serialized.data['hash'], image.hash)

    entity = Entity(name='Test Hase')
    db.session.add(entity)
    db.session.commit()

    coll = Collection(name='Test Collection', entity_ref=entity)
    db.session.add(coll)
    db.session.commit()

    container = Container(name='Test Container', collection_ref=coll)
    db.session.add(container)
    db.session.commit()

    image.container_id=container.id
    db.session.commit()

    serialized = schema.dump(image)
    self.assertDictEqual(serialized.errors, {})
    self.assertEqual(serialized.data['container'], str(container.id))
    self.assertEqual(serialized.data['containerName'], container.name)
    self.assertEqual(serialized.data['collection'], str(coll.id))
    self.assertEqual(serialized.data['collectionName'], coll.name)
    self.assertEqual(serialized.data['entity'], str(entity.id))
    self.assertEqual(serialized.data['entityName'], entity.name)
    self.assertIsNone(serialized.data['deletedAt'])
    self.assertFalse(serialized.data['deleted'])

  def test_schema_tags(self):
    schema = ImageSchema()
    image = _create_image()[0]

    tag1 = Tag(name='v1', image_ref=image)
    db.session.add(tag1)
    db.session.commit()
    tag2 = Tag(name='v2', image_ref=image)
    db.session.add(tag2)
    db.session.commit()

    serialized = schema.dump(image)
    self.assertDictEqual(serialized.errors, {})
    self.assertListEqual(serialized.data['tags'], ['v1', 'v2'])
    Tag.__table__.delete()
  
  def _get_test_path(self, name):
    return os.path.join(os.path.dirname(__file__), "../share/", name)

  @unittest.skipIf(which("singularity") is None, "singularity not installed")
  def test_inspect(self):
    image = _create_image()[0]
    image.location = self._get_test_path("busybox.sif")
    image.uploaded = True
    db.session.commit()

    deffile = image.inspect()
    self.assertEqual(deffile, 'bootstrap: docker\nfrom: busybox\n\n')

  def test_check_file_file_not_found(self):
    image = _create_image()[0]
    image.location = self._get_test_path("migibtsnet.sif")
    image.uploaded = True
    db.session.commit()

    with self.assertRaisesRegex(Exception, r"Image file.*does not exist"):
      image._check_file()

  def test_check_file_not_uploaded(self):
    image = _create_image()[0]
    image.uploaded = False
    db.session.commit()

    with self.assertRaisesRegex(Exception, r"Image is not uploaded yet"):
      image._check_file()

  @unittest.skipIf(which("singularity") is None, "singularity not installed")
  def test_signed(self):
    self.app.config['KEYSERVER_URL']='http://nonexistent/'
    image = _create_image()[0]
    image.location = self._get_test_path("busybox_signed.sif")
    image.uploaded = True
    db.session.commit()

    sigdata = image.check_signature()
    self.assertEqual(sigdata['Signatures'], 1)
    self.assertIsNone(sigdata['SignerKeys'])
    self.assertEqual(sigdata['Reason'], 'Unknown')

  @unittest.skipIf(which("singularity") is None, "singularity not installed")
  def test_signature_fail(self):
    self.app.config['KEYSERVER_URL']='http://nonexistent/'
    image = _create_image()[0]
    # just something that is not a SIF
    image.location = __file__
    image.uploaded = True
    db.session.commit()

    with self.assertRaisesRegex(Exception, r'invalid SIF file'):
      image.check_signature()

  @unittest.skipIf(which("singularity") is None, "singularity not installed")
  def test_signature_unsigned(self):
    self.app.config['KEYSERVER_URL']='http://nonexistent/'
    image = _create_image()[0]
    image.location = self._get_test_path("busybox.sif")
    image.uploaded = True
    db.session.commit()

    sigdata = image.check_signature()
    self.assertEqual(sigdata['Signatures'], 0)
    self.assertIsNone(sigdata['SignerKeys'])
    self.assertEqual(sigdata['Reason'], 'Unsigned')

  @unittest.skipIf(which("singularity") is None, "singularity not installed")
  def test_signed_pubkey(self):
    self.app.config['KEYSERVER_URL']='http://nonexistent/'
    imp = subprocess.run(["singularity", "keys", "import", self._get_test_path("testhase-pub.asc")], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if imp.returncode != 0:
      raise Exception(f"Test key import error: {imp.stderr}")
    image = _create_image()[0]
    image.location = self._get_test_path("busybox_signed.sif")
    image.uploaded = True
    db.session.commit()

    sigdata = image.check_signature()
    self.assertEqual(sigdata['Signatures'], 1)
    self.assertDictContainsSubset({ 'Partition': 'Def.FILE', 'DataCheck': True }, sigdata['SignerKeys'][0]['Signer'])
    rmtree(os.path.expanduser("~/.singularity/sypgp"))
  
  def test_signed_mock(self):
    image = _create_image(media_type=Image.singularity_media_type)[0]
    image.location = self._get_test_path("busybox_signed.sif")
    image.uploaded = True
    db.session.commit()

    with mock.patch('subprocess.run') as mock_sig:
      mock_sig.return_value = mock.Mock(returncode=0, stdout='{ "Passed": true, "Signatures": 1 }')
      sigdata = image.check_signature()
      mock_sig.assert_called()
      self.assertTrue(image.signed)
      self.assertTrue(image.signatureVerified)

  def test_skip_signature_non_singularity(self):
    image = _create_image(media_type='oink')[0]
    image.location = self._get_test_path("busybox_signed.sif")
    image.uploaded = True
    db.session.commit()

    with mock.patch('subprocess.run') as mock_sig:
      sigdata = image.check_signature()
      mock_sig.assert_not_called()
      self.assertDictEqual(sigdata, {'Passed': False, 'Reason': 'NotApplicable'})
      


  
  def test_media_type(self):
    image = _create_image()[0]

    self.assertFalse(image.hide)

    image.media_type='testhase'
    self.assertTrue(image.hide)
    image.media_type='application/vnd.sylabs.sif.layer.v1.sif'
    self.assertFalse(image.hide)

    image.hide = True
    image.media_type = None
    self.assertFalse(image.hide)

  def test_make_filename(self):
    image = _create_image()[0]
    fn = image.make_filename()
    self.assertEquals(fn, f"{image.hash}.sif")

    image.media_type='grunz'
    fn = image.make_filename()
    self.assertEquals(fn, f"{image.hash}")
  
  def test_make_prettyname(self):
    image = _create_image()[0]
    fn = image.make_prettyname('v1')
    self.assertEquals(fn, f"{image.entityName()}/{image.collectionName()}/{image.containerName()}_v1.sif")

    image.media_type='grunz'
    fn = image.make_prettyname('v1')
    self.assertEquals(fn, f"{image.entityName()}/{image.collectionName()}/{image.containerName()}_v1")