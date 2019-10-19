from mongoengine import Document, StringField, ReferenceField

class Tag(Document):
  name = StringField(required=True)
  image_ref = ReferenceField('Image')
