from Hinkskalle.models.Image import Image
from Hinkskalle import db
from datetime import datetime
from sqlalchemy.orm import validates
from Hinkskalle.models.Manifest import Manifest

class Tag(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)

  image_id = db.Column(db.Integer, db.ForeignKey('image.id'), nullable=False)
  image_ref = db.relationship('Image', back_populates='tags_ref')

  manifest_id = db.Column(db.Integer, db.ForeignKey('manifest.id'), nullable=True)
  manifest_ref: Manifest = db.relationship('Manifest', back_populates='tags')

  createdAt = db.Column(db.DateTime, default=datetime.now)
  createdBy = db.Column(db.String(), db.ForeignKey('user.username'))
  updatedAt = db.Column(db.DateTime, onupdate=datetime.now)

  owner = db.relationship('User', back_populates='tags')

  @validates('name')
  def convert_lower(self, key, value):
    return value.lower()

  def generate_manifest(self) -> Manifest:
    if not self.image_ref.media_type == Image.singularity_media_type:
      raise Exception(f"Refusing to create manifest for non-singularity media type {self.image_ref.media_type}")
    data = {
      'schemaVersion': 2,
      'config': {
        'mediaType': 'application/vnd.sylabs.sif.config.v1',
      },
      'layers': [{
        # see https://github.com/opencontainers/image-spec/blob/master/descriptor.md
        'mediaType': self.image_ref.media_type,
        'digest': self.image_ref.hash.replace('sha256.', 'sha256:'),
        'size': self.image_ref.size,
        # singularity does not pull without a name
        # could provide more annotations!
        'annotations': {
          # singularity oras pull needs this!
          'org.opencontainers.image.title': self.image_ref.container_ref.name,
        }
      }]
    }
    with db.session.no_autoflush:
      manifest = Manifest(content=data)
      existing = Manifest.query.filter(Manifest.hash == manifest.hash).first()
      if existing:
        manifest = existing
    
    db.session.add(manifest)
    self.manifest_ref=manifest
    db.session.commit()
    
    return manifest



  __table_args__ = (db.UniqueConstraint('name', 'image_id', name='name_image_id_idx'),)