from typing import Tuple
from Hinkskalle.models.Image import Image
import tempfile
from Hinkskalle.models.Entity import Entity
import os.path

from Hinkskalle.tests.route_base import RouteBase
from Hinkskalle.tests._util import _create_image, _create_container, _create_user

from Hinkskalle import db
from Hinkskalle.models import ImageUploadUrl, UploadStates, UploadTypes
from ..test_imagefiles import _prepare_img_data


class TestOrasPushChunked(RouteBase):
  def test_push_chunks_get_session(self):
    container = _create_container()[0]
    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/{container.entityName}/{container.collectionName}/{container.name}/blobs/uploads/", headers={'Content-Length': 0})
    self.assertEqual(ret.status_code, 202)
    upload_id = ret.headers.get('location').split('/')[-1]

    db_upload = ImageUploadUrl.query.get(upload_id)
    self.assertIsNotNone(db_upload)
    self.assertEqual(db_upload.state, UploadStates.initialized)
    self.assertEqual(db_upload.type, UploadTypes.undetermined)
    self.assertTrue(os.path.exists(db_upload.path))
    self.assertNotEqual(db_upload.image_ref.uploadState, UploadStates.completed)

  def test_push_chunks_init(self):
    image = _create_image()[0]
    upload = ImageUploadUrl(
      image_ref = image,
      state = UploadStates.initialized,
      type = UploadTypes.undetermined,
      path = '/test/hase'
    )
    db.session.add(upload)
    db.session.commit()
    upload_id = upload.id

    with self.fake_admin_auth():
      ret = self.client.patch(f"/v2/__uploads/{upload.id}", data='oink', headers={ 'Content-Type': 'application/octet-stream'})
    self.assertEqual(ret.status_code, 202)

    db_upload: ImageUploadUrl = ImageUploadUrl.query.get(upload_id)
    self.assertEqual(db_upload.type, UploadTypes.multipart)
    self.assertEqual(db_upload.state, UploadStates.uploading)

    self.assertTrue(os.path.isdir(db_upload.path))

    db_chunk = db_upload.parts_ref.filter(ImageUploadUrl.partNumber==1).first()
    self.assertEqual(db_chunk.type, UploadTypes.multipart_chunk)
    self.assertEqual(db_chunk.state, UploadStates.uploaded)
    self.assertEqual(db_chunk.size, 4)
    self.assertTrue(os.path.exists(db_chunk.path))
    with open(db_chunk.path, 'rb') as read_fh:
      content = read_fh.read()
      self.assertEqual(content, b'oink')

    next_chunk = db_upload.parts_ref.filter(ImageUploadUrl.partNumber==2).first()
    self.assertEqual(next_chunk.type, UploadTypes.multipart_chunk)
    self.assertEqual(next_chunk.state, UploadStates.initialized)

    location = ret.headers.get('location', '')
    self.assertRegexpMatches(location, rf'/{db_upload.id}/{next_chunk.id}$')

  def test_push_chunks_init_content_range(self):
    image = _create_image()[0]
    upload = ImageUploadUrl(
      image_ref = image,
      state = UploadStates.initialized,
      type = UploadTypes.undetermined,
      path = '/test/hase'
    )
    db.session.add(upload)
    db.session.commit()
    upload_id = upload.id

    with self.fake_admin_auth():
      ret = self.client.patch(f"/v2/__uploads/{upload.id}", data='oink', headers={ 'Content-Type': 'application/octet-stream', 'Content-Range': '0-3'})
    self.assertEqual(ret.status_code, 202)

  def test_push_chunks_init_content_range_invalid_begin(self):
    image = _create_image()[0]
    upload = ImageUploadUrl(
      image_ref = image,
      state = UploadStates.initialized,
      type = UploadTypes.undetermined,
      path = '/test/hase'
    )
    db.session.add(upload)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.patch(f"/v2/__uploads/{upload.id}", data='oink', headers={ 'Content-Type': 'application/octet-stream', 'Content-Range': '3-99'})
    self.assertEqual(ret.status_code, 416)

  def test_push_chunks_init_content_range_invalid_length(self):
    image = _create_image()[0]
    upload = ImageUploadUrl(
      image_ref = image,
      state = UploadStates.initialized,
      type = UploadTypes.undetermined,
      path = '/test/hase'
    )
    db.session.add(upload)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.patch(f"/v2/__uploads/{upload.id}", data='oink', headers={ 'Content-Type': 'application/octet-stream', 'Content-Range': '0-5'})
    self.assertEqual(ret.status_code, 400)

  def test_push_chunks_continue(self):
    image = _create_image()[0]
    upload = ImageUploadUrl(
      image_ref = image,
      state = UploadStates.uploading,
      type = UploadTypes.multipart,
      path = tempfile.mkdtemp(),
    )
    chunk = ImageUploadUrl(
      image_ref = image,
      state = UploadStates.initialized,
      type = UploadTypes.multipart_chunk,
      path = tempfile.mkstemp(dir=upload.path)[1],
      partNumber = 2,
      parent_ref=upload,
    )
    db.session.add(upload)
    db.session.add(chunk)
    db.session.commit()
    chunk_id = chunk.id

    with self.fake_admin_auth():
      ret = self.client.patch(f"/v2/__uploads/{upload.id}/{chunk.id}", data='oink', headers={ 'Content-Type': 'application/octet-stream'})
    self.assertEqual(ret.status_code, 202)


  def test_push_chunk_finish(self):
    self.app.config['IMAGE_PATH'] = tempfile.mkdtemp()
    test_data = b'grunz oink muh MUH'
    image, upload, last_chunk, complete_digest = _prepare_chunked_upload(test_data)
    upload_id = upload.id
    image_id = image.id

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/__uploads/{upload.id}/{last_chunk.id}?digest={complete_digest.replace('sha256.', 'sha256:')}")
    self.assertEqual(ret.status_code, 201)

    db_image: Image = Image.query.get(image_id)
    self.assertEqual(db_image.uploadState, UploadStates.completed)
    self.assertTrue(db_image.hash, complete_digest)

    with open(db_image.location, 'rb') as read_fh:
      content = read_fh.read()
      self.assertEqual(content, test_data)

    db_upload = ImageUploadUrl.query.get(upload_id)
    self.assertEqual(db_upload.state, UploadStates.completed)
    for chunk in db_upload.parts_ref:
      self.assertEqual(chunk.state, UploadStates.completed)

    header_digest = ret.headers.get('docker-content-digest', '')
    self.assertEqual(header_digest, complete_digest.replace('sha256.', 'sha256:'))

  def test_push_chunk_finish_quota(self):
    self.app.config['IMAGE_PATH'] = tempfile.mkdtemp()
    test_data = b'grunz oink muh MUH'
    image, upload, last_chunk, complete_digest = _prepare_chunked_upload(test_data)
    entity = image.container_ref.collection_ref.entity_ref
    entity_id = entity.id

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/__uploads/{upload.id}/{last_chunk.id}?digest={complete_digest.replace('sha256.', 'sha256:')}")
    self.assertEqual(ret.status_code, 201)
    entity = Entity.query.get(entity_id)
    self.assertEqual(entity.used_quota, len(test_data))

  def test_push_chunk_finish_quota_check(self):
    self.app.config['IMAGE_PATH'] = tempfile.mkdtemp()
    test_data = b'grunz oink muh MUH'
    user = _create_user()
    image, upload, last_chunk, complete_digest = _prepare_chunked_upload(test_data)
    entity = image.container_ref.collection_ref.entity_ref
    entity.owner = user
    user.quota = len(test_data)-1
    db.session.commit()
    image_id = image.id
    upload_id = upload.id

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/__uploads/{upload.id}/{last_chunk.id}?digest={complete_digest.replace('sha256.', 'sha256:')}")
    self.assertEqual(ret.status_code, 413)
    image = Image.query.get(image_id)
    self.assertNotEqual(image.uploadState, UploadStates.completed)
    upload = ImageUploadUrl.query.get(upload_id)
    self.assertEqual(upload.state, UploadStates.failed)

  def test_push_chunk_finish_checksum(self):
    self.app.config['IMAGE_PATH'] = tempfile.mkdtemp()
    test_data = b'grunz oink muh MUH'
    image, upload, last_chunk, complete_digest = _prepare_chunked_upload(test_data)

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/__uploads/{upload.id}/{last_chunk.id}?digest={complete_digest.replace('sha256.', 'sha256:')}oink")
    self.assertEqual(ret.status_code, 400)

  def test_push_chunk_finish_data(self):
    self.app.config['IMAGE_PATH'] = tempfile.mkdtemp()
    test_data = b'grunz oink muh MUH'
    image, upload, last_chunk, _ = _prepare_chunked_upload(test_data)
    complete_data, complete_digest = _prepare_img_data(test_data + b' MMMUUUH')
    image_id = image.id
    last_chunk_id = last_chunk.id

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/__uploads/{upload.id}/{last_chunk.id}?digest={complete_digest.replace('sha256.', 'sha256:')}", data=' MMMUUUH', headers={'Content-Type': 'application/octet-stream'})
    self.assertEqual(ret.status_code, 201)
    db_chunk = ImageUploadUrl.query.get(last_chunk_id)
    self.assertEqual(db_chunk.size, 8)
    self.assertEqual(db_chunk.state, UploadStates.completed)

    db_image = Image.query.get(image_id)
    with open(db_image.location, 'rb') as read_fh:
      content = read_fh.read()
      self.assertEqual(content, complete_data)

  def test_push_chunk_finish_reuse(self):
    self.app.config['IMAGE_PATH'] = tempfile.mkdtemp()
    test_data = b'grunz oink muh MUH'
    image, upload, last_chunk, complete_digest = _prepare_chunked_upload(test_data)
    other_image = _create_image(hash='muh')[0]
    other_image.container_id=image.container_id
    other_image.hash = complete_digest
    db.session.commit()

    upload_id = upload.id
    image_id = image.id
    other_image_id = other_image.id

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/__uploads/{upload.id}/{last_chunk.id}?digest={complete_digest.replace('sha256.', 'sha256:')}")
    print(ret.get_json())
    self.assertEqual(ret.status_code, 201)

    db_upload = ImageUploadUrl.query.get(upload_id)
    self.assertEqual(db_upload.image_id, other_image_id)

    self.assertIsNone(Image.query.get(image_id))








def _prepare_chunked_upload(test_data: bytes) -> Tuple[Image, ImageUploadUrl, ImageUploadUrl, str]:
  image = _create_image()[0]

  complete_data, complete_digest = _prepare_img_data(data=test_data)
  
  temp_path = tempfile.mkdtemp()
  upload = ImageUploadUrl(
    image_ref = image,
    path = temp_path,
    state=UploadStates.uploading,
    type=UploadTypes.multipart,
  )
  db.session.add(upload)
  chunks = []
  for item in [ complete_data[i:i+5] for i in range(0, len(complete_data), 5)]:
    img_data, digest = _prepare_img_data(data=item)
    _, temp_file = tempfile.mkstemp(dir=temp_path)
    with open(temp_file, 'wb') as temp_fh:
      temp_fh.write(img_data)
    part = ImageUploadUrl(
      image_id = image.id,
      path = temp_file,
      partNumber = len(chunks)+1,
      parent_ref = upload,
      state = UploadStates.uploaded,
      type = UploadTypes.multipart_chunk,
      size = len(img_data),
    )
    db.session.add(part)
    chunks.append(part)
  
  last_chunk = ImageUploadUrl(
    image_id = image.id,
    partNumber = len(chunks)+1,
    parent_ref = upload,
    path = tempfile.mkstemp(dir=temp_path)[1],
    state = UploadStates.initialized,
    type = UploadTypes.multipart_chunk,
  )
  db.session.add(last_chunk)
  db.session.commit()
  return image, upload, last_chunk, complete_digest, 
