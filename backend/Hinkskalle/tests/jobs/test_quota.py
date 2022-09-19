from unittest import mock

from ..job_base import JobBase

from Hinkskalle import db
from Hinkskalle.models.Adm import Adm, AdmKeys
from Hinkskalle.models.Entity import Entity
from Hinkskalle.models.Image import UploadStates
from Hinkskalle.models.User import User

from .._util import _create_user, _create_image, default_entity_name

class TestQuotaJob(JobBase):
  def test_job(self):
    from Hinkskalle.util.jobs import update_quotas
    job = self.queue.enqueue(update_quotas)
    self.assertTrue(job.is_finished)
    self.assertEqual(job.meta['progress'], 'done')
    self.assertEqual(job.meta['result']['updated'], 0)

    adm = Adm.query.filter(Adm.key == AdmKeys.check_quotas).first()
    self.assertDictEqual(adm.val, job.meta['result'])
  
  @mock.patch.object(Entity, 'calculate_used')
  @mock.patch.object(User, 'calculate_used')
  def test_check(self, mock_user_calc: mock.MagicMock, mock_entity_calc: mock.MagicMock):
    user1 = _create_user('test.hase1')
    user2 = _create_user('test.hase2')
    ent1 = Entity(name=default_entity_name)
    ent2 = Entity(name='test.hase2')
    db.session.add(ent1)
    db.session.add(ent2)

    img1 = _create_image(postfix='1', location='/da/ham1', size=1234, uploadState=UploadStates.completed)[0]
    img2 = _create_image(postfix='2', location='/da/ham2', size=2345, uploadState=UploadStates.completed)[0]
    img2_dup = _create_image(postfix='2_dup', location='/da/ham2', size=2345, uploadState=UploadStates.completed)[0]
    img3_inv = _create_image(postfix='3_inv', location='/da/ham3', size=3456, uploadState=UploadStates.broken)[0]
    img4 = _create_image(postfix='4', location='/da/ham4', size=4567, uploadState=UploadStates.completed)[0]

    mock_user_calc.side_effect = [ 777, 9876 ]
    mock_entity_calc.side_effect = [ 666, 1234 ]

    from Hinkskalle.util.jobs import update_quotas
    job = self.queue.enqueue(update_quotas)
    print(job.meta)
    self.assertEqual(job.meta['progress'], 'done')
    self.assertEqual(job.meta['result']['updated'], 4)
    self.assertEqual(job.meta['result']['total_space'], img1.size+img2.size+img4.size)
    mock_entity_calc.assert_has_calls([mock.call(), mock.call()])
    mock_user_calc.assert_has_calls([mock.call(), mock.call()])




  
