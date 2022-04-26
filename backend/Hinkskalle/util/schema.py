from __future__ import annotations
from marshmallow import Schema, fields
from marshmallow.utils import is_aware
from dateutil.tz import tzlocal
import datetime as dt

class BaseSchema(Schema):
  class Meta:
    datetimeformat = 'iso'

class LocalDateTime(fields.AwareDateTime):
    def __init__(
        self,
        format: str | None = None,
        *,
        default_timezone: dt.tzinfo | None = tzlocal(),
        **kwargs,
    ):
        super().__init__(format=format, **kwargs)
        self.default_timezone = default_timezone

    def _serialize(self, value, attr, obj, **kwargs):
      if value is not None and not is_aware(value):
        lvalue = value.replace(tzinfo=self.default_timezone)
      else:
        lvalue = value
      return super()._serialize(lvalue, attr, obj, **kwargs)
