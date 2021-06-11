import click
from flask import current_app
from flask.cli import AppGroup
from Hinkskalle import db
from Hinkskalle import registry, generator
from Hinkskalle.util.typescript import ModelRenderer
import os
import re
import click

ldap_cli = AppGroup('ldap', short_help='manage ldap integration')

@ldap_cli.command('sync', short_help='synchronize users')
def sync_ldap():
  from Hinkskalle.util.jobs import sync_ldap
  click.echo("starting sync...")
  job = sync_ldap.queue()
  click.echo(f"started sync with job id {job.id}")

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

@current_app.cli.command()
@click.option('--out', default='../frontend/src/store/models.ts', type=click.File(mode='wb'))
def generate_typescript_models(out):
  swagger = generator.generate(registry)
  class_renderer = ModelRenderer()
  models = class_renderer.render(swagger['definitions'])
  out.write(models.encode('utf-8'))