import click
from flask import current_app
from flask.cli import AppGroup
from Hinkskalle import db

db_cli = AppGroup('db')

@db_cli.command('init')
def init_db():
  db.create_all()

current_app.cli.add_command(db_cli)