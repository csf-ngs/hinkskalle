import click
from flask import current_app
from flask.cli import AppGroup
from Hinkskalle import db
from Hinkskalle.models.Entity import Entity
import click
import humanize

ldap_cli = AppGroup('ldap', short_help='manage ldap integration')

@ldap_cli.command('sync', short_help='synchronize users')
def sync_ldap():
  from Hinkskalle.util.jobs import sync_ldap
  click.echo("starting sync...")
  job = sync_ldap.queue()
  click.echo(f"started sync with job id {job.id}")

quota_cli = AppGroup('quota', short_help='manage quotas')
@quota_cli.command('all', short_help='update quota usage of all entities')
def calc_all_quotas():
  from Hinkskalle.util.jobs import update_quotas
  click.echo('starting quota calculation...')
  job = update_quotas.queue()
  click.echo(f"started quota calc job with id {job.id}")

@quota_cli.command('calc', short_help='calc quota usage for entity')
@click.argument('username')
def calc_quota(username: str):
  entity = Entity.query.filter(Entity.name==username).one()
  entity.calculate_used()
  click.echo(f"Entity {entity.name} uses {humanize.naturalsize(entity.used_quota)}/{humanize.naturalsize(entity.quota) if entity.quota else 'unlimited'}")

image_cli = AppGroup('images', short_help='manage images')
@image_cli.command('expire', short_help='delete expired images')
def expire():
  from Hinkskalle.util.jobs import expire_images
  click.echo("starting image expire...")
  job = expire_images.queue()
  click.echo(f"started expire job with id {job.id}")



db_cli = AppGroup('localdb', short_help='hinkskalle specific db commands')

@db_cli.command('init')
def init_db():
  db.create_all()

@db_cli.command('add-user')
@click.option('--username', '-u', help='Username', required=True)
@click.option('--password', '-p', help='Password', required=True)
@click.option('--email', '-e', help='Email', required=True)
@click.option('--firstname', '-f', help='First Name', required=True)
@click.option('--lastname', '-l', help='Last Name', required=True)
@click.option('--admin/--no-admin', default=False, help='Admin Privs')
def add_user(username, password, email, firstname, lastname, admin):
  from Hinkskalle.models import User
  user = User(username=username, email=email, firstname=firstname, lastname=lastname, is_admin=admin)
  user.set_password(password)
  db.session.add(user)
  db.session.commit()

@db_cli.command('remove-user')
@click.argument('username')
def remove_user(username):
  from Hinkskalle.models import User
  user = User.query.filter(User.username==username).one()
  db.session.delete(user)
  db.session.commit()



current_app.cli.add_command(db_cli)
current_app.cli.add_command(ldap_cli)
current_app.cli.add_command(quota_cli)
current_app.cli.add_command(image_cli)

@current_app.cli.command("cron")
def cron():
  from Hinkskalle.util.jobs import rq
  from rq_scheduler import Scheduler
  from datetime import timezone, datetime

  scheduler = Scheduler(connection=rq.connection)
  jobs = scheduler.get_jobs(with_times=True)
  def to_local(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc).astimezone()
  for j in jobs:
    click.echo(f"{j[0].id} last: {to_local(j[0].enqueued_at)} next: {to_local(j[1])}")
