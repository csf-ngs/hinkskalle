from mongoengine import Document, StringField, ReferenceField, DateTimeField
from datetime import datetime

class Tag(Document):
  name = StringField(required=True)
  image_ref = ReferenceField('Image')

  createdAt = DateTimeField(default=datetime.utcnow)
  updatedAt = DateTimeField()
