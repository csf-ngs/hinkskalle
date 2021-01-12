from urllib.parse import urlparse
import tempfile
import datetime
import hashlib
import os.path


from Hinkskalle.tests.route_base import RouteBase

from Hinkskalle.tests.models.test_Image import _create_image

from Hinkskalle.models import Image, ImageUploadUrl, ImageUploadPartUrl, UploadStates, UploadTypes
from Hinkskalle import db


def _prepare_img_data(data=b"Hello Dorian!"):
    img_data=data
    m = hashlib.sha256()
    m.update(img_data)
    return img_data, f"sha256.{m.hexdigest()}"

class TestImagefilesV2(RouteBase):
  def test_push_v2_single(self):
    image, _, _, _ = _create_image()
    img_data = {
      'filesize': 1,
      'sha256sum': 'something',
      'md5sum': 'also something'
    }

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/imagefile/{image.id}", json=img_data)
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertIn('uploadURL', json)
    urlparts = urlparse(json['uploadURL'])
    upload_id = urlparts.path.split('/').pop()

    db_upload = ImageUploadUrl.query.filter(ImageUploadUrl.id==upload_id).first()
    self.assertIsNotNone(db_upload)
    self.assertEqual(db_upload.state, UploadStates.initialized)
    self.assertEqual(db_upload.type, UploadTypes.single)
    self.assertEqual(db_upload.size, img_data['filesize'])
    self.assertEqual(db_upload.sha256sum, img_data['sha256sum'])
    self.assertEqual(db_upload.md5sum, img_data['md5sum'])
    self.assertTrue(abs(db_upload.expiresAt - (datetime.datetime.now()+datetime.timedelta(minutes=5))) < datetime.timedelta(minutes=1))
    self.assertTrue(os.path.exists(db_upload.path))
  
  def test_push_v2_single_do(self):
    image = _create_image()[0]
    img_data, digest = _prepare_img_data()

    _, temp_path = tempfile.mkstemp()
    upload = ImageUploadUrl(
      image_id=image.id,
      path=temp_path,
      sha256sum=digest.replace("sha256.", ""),
      size=len(img_data),
      state=UploadStates.initialized,
    )
    db.session.add(upload)
    db.session.commit()
    upload_id = upload.id

    ret = self.client.put(f"/v2/imagefile/_upload/"+upload_id, data=img_data)
    self.assertEqual(ret.status_code, 200)

    read_upload = ImageUploadUrl.query.get(upload_id)
    self.assertEqual(read_upload.state, UploadStates.uploaded)

    with open(temp_path, "rb") as infh:
      content = infh.read()
      self.assertEqual(content, img_data)

  def test_push_v2_single_do_state_check(self):
    image = _create_image()[0]
    img_data, digest = _prepare_img_data()

    temp_path = tempfile.mkdtemp()
    upload = ImageUploadUrl(
      image_id=image.id,
      path=temp_path,
      sha256sum=digest.replace("sha256.", ""),
      size=len(img_data),
      state=UploadStates.uploading,
    )
    db.session.add(upload)
    db.session.commit()

    ret = self.client.put(f"/v2/imagefile/_upload/"+upload.id, data=img_data)
    self.assertEqual(ret.status_code, 406)

  def test_push_v2_single_do_size_check(self):
    image = _create_image()[0]
    img_data, digest = _prepare_img_data()

    _, temp_path = tempfile.mkstemp()
    upload = ImageUploadUrl(
      image_id=image.id,
      path=temp_path,
      sha256sum=digest.replace("sha256.", ""),
      size=len(img_data)+2,
      state=UploadStates.initialized,
    )
    db.session.add(upload)
    db.session.commit()

    ret = self.client.put(f"/v2/imagefile/_upload/"+upload.id, data=img_data)
    self.assertEqual(ret.status_code, 422)

  def test_push_v2_single_do_checksum_check(self):
    image = _create_image()[0]
    img_data, digest = _prepare_img_data()

    _, temp_path = tempfile.mkstemp()
    upload = ImageUploadUrl(
      image_id=image.id,
      path=temp_path,
      sha256sum=digest.replace("sha256.", "")+'oink',
      size=len(img_data),
      state=UploadStates.initialized,
    )
    db.session.add(upload)
    db.session.commit()

    ret = self.client.put(f"/v2/imagefile/_upload/"+upload.id, data=img_data)
    self.assertEqual(ret.status_code, 422)

  def test_push_v2_single_do_expires_check(self):
    image = _create_image()[0]
    img_data, digest = _prepare_img_data()

    _, temp_path = tempfile.mkstemp()
    upload = ImageUploadUrl(
      image_id=image.id,
      path=temp_path,
      sha256sum=digest.replace("sha256.", ""),
      size=len(img_data),
      state=UploadStates.initialized,
      expiresAt=datetime.datetime.now() - datetime.timedelta(hours=1)
    )
    db.session.add(upload)
    db.session.commit()

    ret = self.client.put(f"/v2/imagefile/_upload/"+upload.id, data=img_data)
    self.assertEqual(ret.status_code, 406)
  
  def test_push_v2_complete(self):
    self.app.config['IMAGE_PATH']=tempfile.mkdtemp()
    image = _create_image()[0]
    image_id = image.id
    img_data, digest = _prepare_img_data()
    _, temp_path = tempfile.mkstemp()
    with open(temp_path, "wb") as temp_fh:
      temp_fh.write(img_data)

    upload = ImageUploadUrl(
      image_id = image.id,
      path = temp_path,
      sha256sum=digest.replace("sha256.", ""),
      size=len(img_data),
      state=UploadStates.uploaded,
    )
    db.session.add(upload)
    db.session.commit()
    upload_id = upload.id

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_complete", json={})
    self.assertEqual(ret.status_code, 200)

    read_image = Image.query.get(image_id)
    self.assertTrue(read_image.uploaded)
    self.assertTrue(os.path.exists(read_image.location))
    self.assertEqual(read_image.size, os.path.getsize(read_image.location))

    with open(read_image.location, "rb") as read_fh:
      read_data = read_fh.read()
      self.assertEqual(read_data, img_data)
    
    read_upload = ImageUploadUrl.query.get(upload_id)
    self.assertEqual(read_upload.state, UploadStates.completed)

  def test_push_v2_complete_upload_state(self):
    image = _create_image()[0]
    upload = ImageUploadUrl(
      image_id = image.id,
      path = '/some/where',
      state=UploadStates.uploading,
    )
    db.session.add(upload)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_complete", json={})
    self.assertEqual(ret.status_code, 404)

  def test_push_v2_complete_no_upload(self):
    image = _create_image()[0]
    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_complete", json={})
    self.assertEqual(ret.status_code, 404)
  
  def test_push_v2_complete_noauth(self):
    ret = self.client.put(f"/v2/imagefile/whatever/_complete", json={})
    self.assertEqual(ret.status_code, 401)


  def test_push_v2_single_noauth(self):
    ret = self.client.post("/v2/imagefile/whatever", json={'some': 'thing'})
    self.assertEqual(ret.status_code, 401)

  def test_push_v2_single_user(self):
    image, container, coll, entity = _create_image()
    entity.owner=self.user
    coll.owner=self.user
    container.owner=self.user
    db.session.commit()

    img_data = {
      'filesize': 1,
      'sha256sum': 'something',
      'md5sum': 'also something'
    }

    with self.fake_auth():
      ret = self.client.post(f"/v2/imagefile/{image.id}", json=img_data)
    self.assertEqual(ret.status_code, 200)

  def test_push_v2_single_user_other(self):
    image, container, coll, entity = _create_image()
    entity.owner=self.user
    coll.owner=self.user
    container.owner=self.other_user
    db.session.commit()

    img_data = {
      'filesize': 1,
      'sha256sum': 'something',
      'md5sum': 'also something'
    }

    with self.fake_auth():
      ret = self.client.post(f"/v1/imagefile/{image.id}", json=img_data)
    self.assertEqual(ret.status_code, 403)

  def test_push_v2_multi_init(self):
    image = _create_image()[0]
    img_data = {
      'filesize': 128*1024*1024+1,
    }

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/imagefile/{image.id}/_multipart", json=img_data)
    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data')
    self.assertIn('uploadID', json)
    self.assertEqual(json['partSize'], self.app.config.get('MULTIPART_UPLOAD_CHUNK'))
    self.assertEqual(json['totalParts'], 3)
    self.assertDictContainsSubset(json['options'], {})

    upload_id = json['uploadID']

    db_upload = ImageUploadUrl.query.filter(ImageUploadUrl.id==upload_id).first()
    self.assertIsNotNone(db_upload)
    self.assertEqual(db_upload.state, UploadStates.initialized)
    self.assertEqual(db_upload.type, UploadTypes.multipart)
    self.assertEqual(db_upload.size, img_data['filesize'])
    self.assertIsNone(db_upload.sha256sum)
    self.assertTrue(abs(db_upload.expiresAt - (datetime.datetime.now()+datetime.timedelta(minutes=5))) < datetime.timedelta(minutes=1))
    self.assertTrue(os.path.isdir(db_upload.path))
  
  def test_push_v2_multi_init_noauth(self):
    ret = self.client.post(f"/v2/imagefile/whatever/_multipart", json={'what': 'ever'})
    self.assertEqual(ret.status_code, 401)
  
  def test_push_v2_multi_part(self):
    image = _create_image()[0]
    upload = ImageUploadUrl(
      image_id = image.id,
      path = '/some/where',
      totalParts = 2,
      size = 1,
      state=UploadStates.initialized,
      type=UploadTypes.multipart,
    )
    db.session.add(upload)
    db.session.commit()

    part_data = {
      "uploadID": upload.id,
      "partSize": 1,
      "partNumber": 1,
      "sha256sum": 'something',
    }

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_multipart", json=part_data)

    self.assertEqual(ret.status_code, 200)
    self.assertIn('uploadURL', ret.get_json().get('data'))

    urlparts = urlparse(json['uploadURL'])
    part_id = urlparts.path.split('/').pop()

    part = ImageUploadPartUrl.query.get(part_id)
    self.assertEqual(part.size, part_data['size'])
    self.assertEqual(part.sha256sum, part_data['sha256sum'])
    self.assertEqual(part.upload_id, upload.id)


