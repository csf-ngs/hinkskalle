from unittest import mock

from ..job_base import JobBase
from .._util import _create_image, _fake_img_file

from datetime import datetime, timedelta

from Hinkskalle import db
from Hinkskalle.models.Adm import Adm, AdmKeys

from Hinkskalle.util.jobs import expire_images

class TestQuotaJob(JobBase):
  def test_job(self):
    job = self.queue.enqueue(expire_images)
    self.assertTrue(job.is_finished)
    self.assertEqual(job.meta['progress'], 'done')
    self.assertEqual(job.meta['result']['updated'], 0)

    adm = Adm.query.filter(Adm.key == AdmKeys.expire_images).first()
    self.assertDictEqual(adm.val, job.meta['result'])
  
  def test_expire(self):
    img1 = _create_image(hash='1', expiresAt=datetime.now() - timedelta(days=1))[0]
    _fake_img_file(img1)
    img2 = _create_image(hash='2', expiresAt=datetime.now() + timedelta(days=1))[0]
    _fake_img_file(img2)

    with mock.patch('os.unlink') as mock_unlink:
      job = self.queue.enqueue(expire_images)
    mock_unlink.assert_called_once_with(img1.location)
    self.assertEqual(job.meta['progress'], 'done')
    self.assertEqual(job.meta['result']['updated'], 1)
    self.assertEqual(job.meta['result']['space_reclaimed'], img1.size)

    self.assertFalse(img1.uploaded)
    self.assertTrue(img2.uploaded)

  def test_expire_not_uploaded(self):
    img1 = _create_image(hash='1', expiresAt=datetime.now() - timedelta(days=1))[0]
    img2 = _create_image(hash='2', expiresAt=datetime.now() + timedelta(days=1))[0]

    with mock.patch('os.unlink') as mock_unlink:
      job = self.queue.enqueue(expire_images)
    mock_unlink.assert_not_called()
    self.assertEqual(job.meta['progress'], 'done')
    self.assertEqual(job.meta['result']['updated'], 0)

  def test_expire_file_not_found(self):
    img1 = _create_image(hash='1', size=99, uploaded=True, location='/da/ham', expiresAt=datetime.now() - timedelta(days=1))[0]

    job = self.queue.enqueue(expire_images)
    self.assertEqual(job.meta['progress'], 'done')
    self.assertEqual(job.meta['result']['updated'], 1)
    self.assertEqual(job.meta['result']['space_reclaimed'], 0)

  def test_expire_size_none(self):
    img1 = _create_image(hash='1', expiresAt=datetime.now() - timedelta(days=1))[0]
    tmpf = _fake_img_file(img1, data=b'something')
    img1.size = None
    db.session.commit()

    with mock.patch('os.unlink') as mock_unlink:
      job = self.queue.enqueue(expire_images)
    mock_unlink.assert_called_once_with(tmpf.name)
    self.assertEqual(job.meta['progress'], 'done')
    self.assertEqual(job.meta['result']['updated'], 1)
    self.assertEqual(job.meta['result']['space_reclaimed'], 9)

  def test_expire_location_none(self):
    img1 = _create_image(hash='1', uploaded=True, location=None, expiresAt=datetime.now() - timedelta(days=1))[0]

    with mock.patch('os.unlink') as mock_unlink:
      job = self.queue.enqueue(expire_images)
    mock_unlink.assert_not_called()
    self.assertEqual(job.meta['progress'], 'done')
    self.assertEqual(job.meta['result']['updated'], 1)
    self.assertEqual(job.meta['result']['space_reclaimed'], 0)

    self.assertFalse(img1.uploaded)