from unittest import mock

from ..job_base import JobBase

from Hinkskalle import db
from Hinkskalle.models.Adm import Adm, AdmKeys
from Hinkskalle.models.Entity import Entity

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
  def test_check(self, mock_calc: mock.MagicMock):
    ent1 = Entity(name='test.hase1')
    ent2 = Entity(name='test.hase2')
    db.session.add(ent1)
    db.session.add(ent2)
    mock_calc.side_effect = [ 666, 1234 ]
    from Hinkskalle.util.jobs import update_quotas
    job = self.queue.enqueue(update_quotas)
    self.assertEqual(job.meta['progress'], 'done')
    self.assertEqual(job.meta['result']['updated'], 2)
    self.assertEqual(job.meta['result']['total_space'], 666+1234)
    mock_calc.assert_has_calls([mock.call(), mock.call()])




  
