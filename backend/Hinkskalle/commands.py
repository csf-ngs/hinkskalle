import click
from flask import current_app
from flask.cli import AppGroup
from Hinkskalle import db
import os
import re

db_cli = AppGroup('local_db', short_help='hinkskalle specific db commands')

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


@db_cli.command('migrate-mongo')
@click.option('--mongodb-host', '-m', envvar='MONGODB_HOST', help='MongoDB URI (can also read from MONGDB_HOST env)')
@click.confirmation_option(prompt='This will kill your database! Do it?')
def migrate_mongo(mongodb_host):
  from pymongo import MongoClient
  from Hinkskalle.models import Entity, Collection, Container, Image, Tag

  db.drop_all()
  db.create_all()

  connect_url = re.sub('/[^/]+:@', '/', mongodb_host)
  db_name = connect_url.split('/')[-1]
  current_app.logger.info(f"connecting to mongodb @ {connect_url} (db {db_name})")

  client = MongoClient(connect_url)
  mongodb = client[db_name]

  current_app.logger.info(f"migrating {mongodb.entity.count_documents({})} entities...")
  entity_map = {}
  for entity in mongodb.entity.find():
    objid = str(entity.pop('_id'))
    db_entity=Entity(**entity)
    current_app.logger.info(f"... {db_entity.name}")
    db.session.add(db_entity)
    entity_map[objid]=db_entity
  
  current_app.logger.info(f"migrating {mongodb.collection.count_documents({})} collections...")
  collection_map = {}
  for collection in mongodb.collection.find():
    objid = str(collection.pop('_id'))
    entity_id = str(collection.pop('entity_ref'))

    db_collection=Collection(**collection)
    db_collection.entity_ref=entity_map.get(entity_id)
    current_app.logger.info(f"... {db_collection.name}")
    db.session.add(db_collection)
    collection_map[objid]=db_collection
  
  current_app.logger.info(f"migrating {mongodb.container.count_documents({})} containers...")
  container_map = {}
  for container in mongodb.container.find():
    objid = str(container.pop('_id'))
    collection_id = str(container.pop('collection_ref'))

    db_container=Container(**container)
    db_container.collection_ref=collection_map.get(collection_id)
    current_app.logger.info(f"... {db_container.name}")
    db.session.add(db_container)
    container_map[objid]=db_container

  current_app.logger.info(f"migrating {mongodb.image.count_documents({})} images...")
  image_map = {}
  for image in mongodb.image.find():
    objid = str(image.pop('_id'))
    container_id = str(image.pop('container_ref'))

    db_image=Image(**image)
    db_image.container_ref=container_map.get(container_id)
    current_app.logger.info(f"... {db_image.location}")
    db.session.add(db_image)
    image_map[objid]=db_image

  current_app.logger.info(f"migrating {mongodb.tag.count_documents({})} tags...")
  for tag in mongodb.tag.find():
    objid = str(tag.pop('_id'))
    image_id = str(tag.pop('image_ref'))

    db_tag=Tag(**tag)
    db_tag.image_ref=image_map.get(image_id)
    current_app.logger.info(f"... {db_tag.name}")
    db.session.add(db_tag)
  
  db.session.commit()





current_app.cli.add_command(db_cli)
