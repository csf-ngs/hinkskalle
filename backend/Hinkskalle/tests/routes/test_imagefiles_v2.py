from urllib.parse import urlparse
import tempfile
import datetime
import hashlib
import os.path


from Hinkskalle.tests.route_base import RouteBase

from Hinkskalle.tests.models.test_Image import _create_image

from Hinkskalle.models import Image, ImageUploadUrl, UploadStates, UploadTypes
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
    self.assertEqual(ret.headers.get('ETag', None), upload.sha256sum)

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
      owner=self.admin_user,
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
    self.assertEqual(db_upload.createdBy, self.admin_username)
  
  def test_push_v2_multi_init_user(self):
    image, container, _, _ = _create_image()
    container.owner = self.user
    db.session.commit()

    with self.fake_auth():
      ret = self.client.post(f"/v2/imagefile/{image.id}/_multipart", json={ 'filesize': 1 })
    self.assertEqual(ret.status_code, 200)
    db_upload = ImageUploadUrl.query.filter(ImageUploadUrl.id==ret.get_json().get('data').get('uploadID')).first()
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
    json = ret.get_json().get('data')
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
    first_url = ret.get_json().get('data').get('presignedURL')

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image_id}/_multipart", json=part_data)

    self.assertEqual(ret.status_code, 200)
    self.assertEqual(ret.get_json().get('data').get('presignedURL'), first_url)


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
    json = ret.get_json().get('data')

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
  
  def test_push_v2_multi_complete(self):
    self.app.config['IMAGE_PATH']=tempfile.mkdtemp()
    image = _create_image()[0]
    image_id = image.id

    complete_data, complete_digest = _prepare_img_data(data='123'.encode())
    temp_path = tempfile.mkdtemp()
    upload = ImageUploadUrl(
      image_id = image.id,
      path = temp_path,
      sha256sum=complete_digest.replace('sha256.', ''),
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

    complete_data = {
      'uploadID': upload.id,
      'completedParts': [
        { 'partNumber': p.partNumber, 'token': p.sha256sum } for p in parts
      ]
    }

    with self.fake_admin_auth():
      ret = self.client.put(f"/v2/imagefile/{image.id}/_multipart_complete", json=complete_data)
    #self.assertEqual(ret.status_code, 200)
