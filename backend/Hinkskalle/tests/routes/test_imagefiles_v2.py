from Hinkskalle.models.Entity import Entity
from urllib.parse import urlparse
import tempfile
import datetime
import hashlib
import os
import os.path


from ..route_base import RouteBase
from .._util import _create_image, _create_user

from Hinkskalle.models import Image, ImageUploadUrl, UploadStates, UploadTypes, User
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
    json = ret.get_json().get('data') # type: ignore
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

  def test_push_v2_single_quota_check(self):
    user = _create_user()
    user.quota = 1024
    image = _create_image(owner=user)[0]
    img_data = {
      'filesize': 2048,
      'sha256sum': 'something',
      'md5sum': 'also something'
    }

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/imagefile/{image.id}", json=img_data)
    self.assertEqual(ret.status_code, 413)
  
  def test_push_v2_single_readonly(self):
    image = _create_image()[0]
    img_data = {
      'filesize': 1,
      'sha256sum': 'something',
      'md5sum': 'also something'
    }
    image.container_ref.readOnly = True

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/imagefile/{image.id}", json=img_data)
    self.assertEqual(ret.status_code, 406)
  
  def test_push_v2_single_do(self):
    user = _create_user()
    image = _create_image(owner=user)[0]
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
    self.assertEqual(ret.headers.get('ETag', None), upload.sha256sum)

    read_upload = ImageUploadUrl.query.get(upload_id)
    self.assertEqual(read_upload.state, UploadStates.uploaded)

    with open(temp_path, "rb") as infh:
      content = infh.read()
      self.assertEqual(content, img_data)

  def test_push_v2_single_hash_from_image(self):
    image = _create_image()[0]
    img_data, digest = _prepare_img_data()
    image.hash = digest
    db.session.commit()

    _, temp_path = tempfile.mkstemp()
    upload = ImageUploadUrl(
      image_id=image.id,
      path=temp_path,
      sha256sum=None,
      size=len(img_data),
      state=UploadStates.initialized,
    )
    db.session.add(upload)
    db.session.commit()
    upload_id = upload.id

    ret = self.client.put(f"/v2/imagefile/_upload/"+upload_id, data=img_data)
    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.headers.get('ETag', None), upload.sha256sum)

    read_upload = ImageUploadUrl.query.get(upload_id)
    self.assertEqual(read_upload.state, UploadStates.uploaded)


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
      owner=self.admin_user,
      type=UploadTypes.single,
    )
    db.session.add(upload)
    db.session.commit()
    upload_id = upload.id

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_complete", json={})
    self.assertEqual(ret.status_code, 200)

    read_image = Image.query.get(image_id)
    self.assertEqual(read_image.uploadState, UploadStates.completed)
    self.assertTrue(os.path.exists(read_image.location))
    self.assertEqual(read_image.size, os.path.getsize(read_image.location))

    with open(read_image.location, "rb") as read_fh:
      read_data = read_fh.read()
      self.assertEqual(read_data, img_data)
    
    read_upload = ImageUploadUrl.query.get(upload_id)
    self.assertEqual(read_upload.state, UploadStates.completed)

  def test_push_v2_complete_quota(self):
    self.app.config['IMAGE_PATH']=tempfile.mkdtemp()
    user = _create_user()
    image, _, _, entity = _create_image(owner=user)
    entity_id = entity.id
    user_id = user.id
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
      owner=self.admin_user,
      type=UploadTypes.single,
    )
    db.session.add(upload)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_complete", json={})
    self.assertEqual(ret.status_code, 200)
    entity = Entity.query.get(entity_id)
    user = User.query.get(user_id)
    self.assertEqual(entity.used_quota, len(img_data))
    self.assertEqual(user.used_quota, len(img_data))

    data = ret.get_json().get('data') # type: ignore
    self.assertDictEqual(data.get('quota'), {
      'quotaTotal': 0,
      'quotaUsage': len(img_data),
    })

  def test_push_v2_complete_quota_signal(self):
    self.app.config['IMAGE_PATH']=tempfile.mkdtemp()
    img_data, digest = _prepare_img_data()
    user = _create_user()
    user.quota = len(img_data)*2
    image  = _create_image(owner=user)[0]
    _, temp_path = tempfile.mkstemp()
    with open(temp_path, "wb") as temp_fh:
      temp_fh.write(img_data)

    upload = ImageUploadUrl(
      image_id = image.id,
      path = temp_path,
      sha256sum=digest.replace("sha256.", ""),
      size=len(img_data),
      state=UploadStates.uploaded,
      owner=self.admin_user,
      type=UploadTypes.single,
    )
    db.session.add(upload)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_complete", json={})
    self.assertEqual(ret.status_code, 200)

    data = ret.get_json().get('data') # type: ignore
    self.assertDictEqual(data.get('quota'), {
      'quotaTotal': len(img_data)*2,
      'quotaUsage': len(img_data),
    })

  def test_push_v2_complete_quota_check(self):
    self.app.config['IMAGE_PATH']=tempfile.mkdtemp()
    img_data, digest = _prepare_img_data()
    user = _create_user()
    user.quota = len(img_data)-1
    image = _create_image(owner=user)[0]
    image_id = image.id
    _, temp_path = tempfile.mkstemp()
    with open(temp_path, "wb") as temp_fh:
      temp_fh.write(img_data)

    upload = ImageUploadUrl(
      image_id = image.id,
      path = temp_path,
      sha256sum=digest.replace("sha256.", ""),
      size=len(img_data),
      state=UploadStates.uploaded,
      owner=self.admin_user,
      type=UploadTypes.single,
    )
    db.session.add(upload)
    db.session.commit()
    upload_id = upload.id

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_complete", json={})
    self.assertEqual(ret.status_code, 413)
    image = Image.query.get(image_id)
    self.assertEqual(image.uploadState, UploadStates.failed)
    upload = ImageUploadUrl.query.get(upload_id)
    self.assertEqual(upload.state, UploadStates.failed)

  def test_push_v2_complete_upload_state(self):
    image = _create_image()[0]
    upload = ImageUploadUrl(
      image_id = image.id,
      path = '/some/where',
      state=UploadStates.uploading,
      type=UploadTypes.single,
    )
    db.session.add(upload)
    db.session.commit()

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_complete", json={})
    self.assertEqual(ret.status_code, 404)

  def test_push_v2_complete_upload_type(self):
    image = _create_image()[0]
    upload = ImageUploadUrl(
      image_id = image.id,
      path = '/some/where',
      state=UploadStates.uploaded,
      type=UploadTypes.multipart,
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
  
  def test_push_v2_complete_user(self):
    self.app.config['IMAGE_PATH']=tempfile.mkdtemp()
    image, container, _, _ = _create_image()
    container.owner = self.user
    db.session.commit()

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
      owner=self.user,
      type=UploadTypes.single,
    )
    db.session.add(upload)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_complete", json={})
    self.assertEqual(ret.status_code, 200)

  def test_push_v2_complete_user_other(self):
    self.app.config['IMAGE_PATH']=tempfile.mkdtemp()
    image, container, _, _ = _create_image()
    container.owner = self.user
    db.session.commit()

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
      owner=self.other_user,
      type=UploadTypes.single,
    )
    db.session.add(upload)
    db.session.commit()

    with self.fake_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_complete", json={})
    self.assertEqual(ret.status_code, 403)


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
    json = ret.get_json().get('data') # type: ignore
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
    self.assertEqual(db_upload.createdBy, self.admin_username)

  def test_push_v2_multi_init_readonly(self):
    image = _create_image()[0]
    img_data = {
      'filesize': 128*1024*1024+1,
    }
    image.container_ref.readOnly = True

    with self.fake_admin_auth():
      ret = self.client.post(f"/v2/imagefile/{image.id}/_multipart", json=img_data)
    self.assertEqual(ret.status_code, 406)
  
  def test_push_v2_multi_init_user(self):
    image, container, _, _ = _create_image()
    container.owner = self.user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.post(f"/v2/imagefile/{image.id}/_multipart", json={ 'filesize': 1 })
    self.assertEqual(ret.status_code, 200)
    db_upload = ImageUploadUrl.query.filter(ImageUploadUrl.id==ret.get_json().get('data').get('uploadID')).first() # type: ignore
    self.assertEqual(db_upload.createdBy, self.username)

  def test_push_v2_multi_init_user_other(self):
    image, container, _, _ = _create_image()
    container.owner = self.other_user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.post(f"/v2/imagefile/{image.id}/_multipart", json={ 'filesize': 1 })
    self.assertEqual(ret.status_code, 403)

  def test_push_v2_multi_init_noauth(self):
    ret = self.client.post(f"/v2/imagefile/whatever/_multipart", json={'what': 'ever'})
    self.assertEqual(ret.status_code, 401)
  
  def test_push_v2_multi_part(self):
    image = _create_image()[0]
    upload = ImageUploadUrl(
      image_id = image.id,
      path = tempfile.mkdtemp(),
      totalParts = 2,
      size = 1,
      state=UploadStates.initialized,
      type=UploadTypes.multipart,
      owner=self.admin_user,
    )
    db.session.add(upload)
    db.session.commit()
    upload_id = upload.id

    part_data = {
      "uploadID": upload.id,
      "partSize": 1,
      "partNumber": 1,
      "sha256sum": 'something',
    }

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_multipart", json=part_data)

    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore
    self.assertIn('presignedURL', json)

    urlparts = urlparse(json['presignedURL'])
    part_id = urlparts.path.split('/').pop()

    part = ImageUploadUrl.query.get(part_id)
    self.assertEqual(part.state, UploadStates.initialized)
    self.assertEqual(part.parent_ref.state, UploadStates.uploading)
    self.assertEqual(part.size, part_data['partSize'])
    self.assertEqual(part.partNumber, part_data['partNumber'])
    self.assertEqual(part.totalParts, 2)
    self.assertEqual(part.sha256sum, part_data['sha256sum'])
    self.assertEqual(part.parent_id, upload_id)
    self.assertEqual(part.createdBy, self.admin_username)

  def test_push_v2_multi_part_twice(self):
    image = _create_image()[0]
    image_id = image.id
    upload = ImageUploadUrl(
      image_id = image.id,
      path = tempfile.mkdtemp(),
      totalParts = 2,
      size = 1,
      state=UploadStates.initialized,
      type=UploadTypes.multipart,
      owner=self.admin_user,
    )
    db.session.add(upload)
    db.session.commit()
    upload_id = upload.id

    part_data = {
      "uploadID": upload.id,
      "partSize": 1,
      "partNumber": 1,
      "sha256sum": 'something',
    }

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image_id}/_multipart", json=part_data)

    self.assertEqual(ret.status_code, 200)
    first_url = ret.get_json().get('data').get('presignedURL') # type: ignore

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image_id}/_multipart", json=part_data)

    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.get_json().get('data').get('presignedURL'), first_url) # type: ignore


  def test_push_v2_multi_part_invalid_type(self):
    for type in [UploadTypes.single, UploadTypes.multipart_chunk]:
      image = _create_image(hash=f"sha256.oink{type}")[0]
      upload = ImageUploadUrl(
        image_id = image.id,
        path = tempfile.mkdtemp(),
        totalParts = 2,
        size = 1,
        state=UploadStates.initialized,
        type=type,
        owner=self.admin_user,
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

      self.assertEqual(ret.status_code, 406, f"type {type} not acceptable")

  def test_push_v2_multi_part_invalid_state(self):
    for state in [UploadStates.completed, UploadStates.failed]:
      image = _create_image(hash=f"sha256.oink{state}")[0]
      upload = ImageUploadUrl(
        image_id = image.id,
        path = tempfile.mkdtemp(),
        totalParts = 2,
        size = 1,
        state=state,
        type=UploadTypes.multipart,
        owner=self.admin_user,
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

      self.assertEqual(ret.status_code, 406, f"state {state} not acceptable")

  def test_push_v2_multi_part_invalid_part_number(self):
    for number in [-1, 3]:
      image = _create_image(hash=f"sha256.oink-{number}")[0]
      upload = ImageUploadUrl(
        image_id = image.id,
        path = tempfile.mkdtemp(),
        totalParts = 2,
        size = 1,
        state=UploadStates.initialized,
        type=UploadTypes.multipart,
        owner=self.admin_user,
      )
      db.session.add(upload)
      db.session.commit()

      part_data = {
        "uploadID": upload.id,
        "partSize": 1,
        "partNumber": number,
        "sha256sum": 'something',
      }

      with self.fake_admin_auth():
        ret = self.client.put(f"/v2/imagefile/{image.id}/_multipart", json=part_data)

      self.assertEqual(ret.status_code, 406, f"part number {number} not acceptable")

  def test_push_v2_multi_part_user(self):
    image, container, _, _ = _create_image()
    container.owner = self.user
    upload = ImageUploadUrl(
      image_id = image.id,
      path = tempfile.mkdtemp(),
      totalParts = 2,
      size = 1,
      state=UploadStates.initialized,
      type=UploadTypes.multipart,
      owner=self.user,
    )
    db.session.add(upload)
    db.session.commit()

    part_data = {
      "uploadID": upload.id,
      "partSize": 1,
      "partNumber": 1,
      "sha256sum": 'something',
    }

    with self.fake_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_multipart", json=part_data)

    self.assertEqual(ret.status_code, 200)
    json = ret.get_json().get('data') # type: ignore

    urlparts = urlparse(json['presignedURL'])
    part_id = urlparts.path.split('/').pop()

    part = ImageUploadUrl.query.get(part_id)
    self.assertEqual(part.createdBy, self.username)

  def test_push_v2_multi_part_user_other(self):
    image, container, _, _ = _create_image()
    container.owner = self.other_user
    upload = ImageUploadUrl(
      image_id = image.id,
      path = tempfile.mkdtemp(),
      totalParts = 2,
      size = 1,
      state=UploadStates.initialized,
      type=UploadTypes.multipart,
      owner=self.other_user,
    )
    db.session.add(upload)
    db.session.commit()

    part_data = {
      "uploadID": upload.id,
      "partSize": 1,
      "partNumber": 1,
      "sha256sum": 'something',
    }

    with self.fake_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_multipart", json=part_data)

    self.assertEqual(ret.status_code, 403)
  
  def _setup_multi_upload(self):
    self.app.config['IMAGE_PATH']=tempfile.mkdtemp()
    image = _create_image()[0]

    complete_data, complete_digest = _prepare_img_data(data='123'.encode())
    image.hash = complete_digest
    db.session.commit()
    temp_path = tempfile.mkdtemp()
    upload = ImageUploadUrl(
      image_id = image.id,
      path = temp_path,
      size=len(complete_data),
      totalParts=len(complete_data),
      state=UploadStates.uploaded,
      owner=self.admin_user,
      type=UploadTypes.multipart,
    )
    db.session.add(upload)
    db.session.commit()

    parts = []
    for index, item in enumerate(list(complete_data)):
      img_data, digest = _prepare_img_data(data=chr(item).encode())
      _, temp_file = tempfile.mkstemp(dir=temp_path)
      with open(temp_file, "wb") as temp_fh:
        temp_fh.write(img_data)
      part = ImageUploadUrl(
        image_id = image.id,
        path = temp_file,
        size = 1,
        sha256sum = digest.replace('sha256.', ''),
        partNumber = index+1,
        parent_ref = upload,
        owner = self.admin_user,
        state=UploadStates.uploaded,
        type=UploadTypes.multipart_chunk,
      )
      db.session.add(part)
      parts.append(part)
    db.session.commit()
    return image, upload, parts, complete_data

  def test_push_v2_multi_complete(self):
    image, upload, parts, complete_data = self._setup_multi_upload()
    upload_id = upload.id
    image_id = image.id

    complete_json = {
      'uploadID': upload.id,
      'completedParts': [
        { 'partNumber': p.partNumber, 'token': p.sha256sum } for p in parts
      ]
    }

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_multipart_complete", json=complete_json)
    self.assertEqual(ret.status_code, 200)

    data = ret.get_json().get('data') # type: ignore
    self.assertIn('containerUrl', data)
    self.assertIn('quota', data)

    read_image: Image = Image.query.get(image_id)
    self.assertEqual(read_image.uploadState, UploadStates.completed)
    self.assertTrue(os.path.exists(read_image.location))
    self.assertEqual(read_image.size, len(complete_data))
    self.assertEqual(read_image.size, os.path.getsize(read_image.location))

    with open(read_image.location, "rb") as read_fh:
      read_data = read_fh.read()
      self.assertEqual(read_data, complete_data)
    
    read_upload = ImageUploadUrl.query.get(upload_id)
    self.assertEqual(read_upload.state, UploadStates.completed)
  
  def test_push_v2_multi_complete_quota(self):
    image, upload, parts, complete_data = self._setup_multi_upload()
    image.owner = _create_user()
    entity_id = image.container_ref.collection_ref.entity_id
    user_id = image.owner.id

    complete_json = {
      'uploadID': upload.id,
      'completedParts': [
        { 'partNumber': p.partNumber, 'token': p.sha256sum } for p in parts
      ]
    }

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_multipart_complete", json=complete_json)
    self.assertEqual(ret.status_code, 200)
    entity = Entity.query.get(entity_id)
    self.assertEqual(entity.used_quota, len(complete_data))
    user = User.query.get(user_id)
    self.assertEqual(user.used_quota, len(complete_data))

    data = ret.get_json().get('data') # type: ignore
    self.assertDictEqual(data.get('quota'), {
      'quotaTotal': 0,
      'quotaUsage': len(complete_data)
    })

  def test_push_v2_multi_complete_quota_signal(self):
    image, upload, parts, complete_data = self._setup_multi_upload()
    image.owner = _create_user()
    image.owner.quota = len(complete_data)*2
    entity = image.container_ref.collection_ref.entity_ref
    db.session.commit()
    entity_id = entity.id
    user_id = image.owner.id

    complete_json = {
      'uploadID': upload.id,
      'completedParts': [
        { 'partNumber': p.partNumber, 'token': p.sha256sum } for p in parts
      ]
    }

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_multipart_complete", json=complete_json)
    self.assertEqual(ret.status_code, 200)

    data = ret.get_json().get('data') # type: ignore
    self.assertDictEqual(data.get('quota'), {
      'quotaTotal': len(complete_data)*2,
      'quotaUsage': len(complete_data)
    })

    read_user = User.query.get(user_id)
    self.assertEqual(read_user.used_quota, len(complete_data))
    read_entity = Entity.query.get(entity_id)
    self.assertEqual(read_entity.used_quota, len(complete_data))

  def test_push_v2_multi_complete_quota_check(self):
    image, upload, parts, complete_data = self._setup_multi_upload()
    image.owner = _create_user()
    image.owner.quota = len(complete_data)-1
    db.session.commit()
    image_id = image.id
    upload_id = upload.id

    complete_json = {
      'uploadID': upload.id,
      'completedParts': [
        { 'partNumber': p.partNumber, 'token': p.sha256sum } for p in parts
      ]
    }

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_multipart_complete", json=complete_json)
    self.assertEqual(ret.status_code, 413)
    image: Image = Image.query.get(image_id)
    self.assertEqual(image.uploadState, UploadStates.failed)
    upload = ImageUploadUrl.query.get(upload_id)
    self.assertEqual(upload.state, UploadStates.failed)

  def test_push_v2_multi_complete_type_invalid(self):
    image, upload, parts, _ = self._setup_multi_upload()
    upload.type = UploadTypes.single
    db.session.commit()

    complete_json = {
      'uploadID': upload.id,
      'completedParts': [
        { 'partNumber': p.partNumber, 'token': p.sha256sum } for p in parts
      ]
    }

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_multipart_complete", json=complete_json)
    self.assertEqual(ret.status_code, 406)

  def test_push_v2_multi_complete_state_invalid(self):
    image, upload, parts, _ = self._setup_multi_upload()
    parts[0].state=UploadStates.initialized
    db.session.commit()

    complete_json = {
      'uploadID': upload.id,
      'completedParts': [
        { 'partNumber': p.partNumber, 'token': p.sha256sum } for p in parts
      ]
    }

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_multipart_complete", json=complete_json)
    self.assertEqual(ret.status_code, 406)

  def test_push_v2_multi_complete_chunks_missing(self):
    image, upload, parts, _ = self._setup_multi_upload()
    db.session.delete(parts[0])
    db.session.commit()

    complete_json = {
      'uploadID': upload.id,
      'completedParts': [
        { 'partNumber': p.partNumber, 'token': p.sha256sum } for p in parts
      ]
    }

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_multipart_complete", json=complete_json)
    self.assertEqual(ret.status_code, 406)

  def test_push_v2_multi_complete_invalid_checksum(self):
    image, upload, parts, _ = self._setup_multi_upload()
    image.hash = 'sha256.oink'
    db.session.commit()

    complete_json = {
      'uploadID': upload.id,
      'completedParts': [
        { 'partNumber': p.partNumber, 'token': p.sha256sum } for p in parts
      ]
    }

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_multipart_complete", json=complete_json)
    self.assertEqual(ret.status_code, 422)

  def test_push_v2_multi_complete_file_missing(self):
    image, upload, parts, _ = self._setup_multi_upload()
    os.remove(parts[2].path)
    upload_id = upload.id

    complete_json = {
      'uploadID': upload.id,
      'completedParts': [
        { 'partNumber': p.partNumber, 'token': p.sha256sum } for p in parts
      ]
    }

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_multipart_complete", json=complete_json)
    self.assertEqual(ret.status_code, 500)
    db_parts = ImageUploadUrl.query.filter(ImageUploadUrl.parent_id==upload_id).order_by(ImageUploadUrl.partNumber.asc())
    self.assertEqual(db_parts[2].state, UploadStates.failed)
    for part in db_parts[:1]:
      self.assertEqual(part.state, UploadStates.uploaded)
  
  def test_push_v2_multi_complete_user(self):
    image, upload, parts, _ = self._setup_multi_upload()
    image.container_ref.owner = self.user
    upload.owner = self.user
    db.session.commit()

    complete_json = {
      'uploadID': upload.id,
      'completedParts': [
        { 'partNumber': p.partNumber, 'token': p.sha256sum } for p in parts
      ]
    }

    with self.fake_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_multipart_complete", json=complete_json)
    self.assertEqual(ret.status_code, 200)

  def test_push_v2_multi_complete_user_other(self):
    image, upload, parts, _ = self._setup_multi_upload()
    image.container_ref.owner = self.other_user
    upload.owner = self.other_user
    db.session.commit()

    complete_json = {
      'uploadID': upload.id,
      'completedParts': [
        { 'partNumber': p.partNumber, 'token': p.sha256sum } for p in parts
      ]
    }

    with self.fake_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_multipart_complete", json=complete_json)
    self.assertEqual(ret.status_code, 403)

  def test_push_v2_multi_complete_user_noauth(self):
    ret = self.client.put(f"/v2/imagefile/something/_multipart_complete", json={'some': 'thing'})
    self.assertEqual(ret.status_code, 401)
  
  def test_push_v2_multi_abort(self):
    image, upload, _, _ = self._setup_multi_upload()
    image_id = image.id
    upload_id = upload.id

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_multipart_abort", json={ 'uploadID': upload.id })
    self.assertEqual(ret.status_code, 200)

    db_image: Image = Image.query.get(image_id)
    self.assertEqual(db_image.uploadState, UploadStates.failed)
    self.assertIsNone(db_image.location)

    db_upload = ImageUploadUrl.query.get(upload_id)
    self.assertEqual(db_upload.state, UploadStates.failed)
    for part in db_upload.parts_ref:
      self.assertEqual(part.state, UploadStates.failed)
