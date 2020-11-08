{% macro deserialize(fields) -%}
  {% for field in fields -%}
    {% if field.is_reference -%}
      {% if field.multi -%}
        if (!_isNil(json['{{field.name}}'])) obj.{{field.name}} = _map(json['{{field.name}}'], plainTo{{field.type}});
      {% else -%}
        if (!_isNil(json['{{field.name}}'])) obj.{{field.name}} = plainTo{{field.type}}(json['{{field.name}}']);
      {% endif -%}
    {% elif field.type == 'Date | null' -%}
      {% if field.multi -%}
        obj.{{field.name}} = _isNil(json['{{field.name}}']) ? [] : _map(json['{{field.name}}'], d => new Date(d));
      {% else -%}
        obj.{{field.name}} = _isNil(json['{{field.name}}']) ? null : new Date(json['{{field.name}}']);
      {% endif -%}
    {% else -%}
      obj.{{field.name}} = json['{{field.name}}'];
    {% endif -%}
  {% endfor %}
{%- endmacro %}

{% macro serialize(fields) -%}
  {% for field in fields -%}
    {% if not field.readonly -%}
      {% if field.is_reference -%}
        {% if field.multi -%}
          if (unroll) json['{{field.name}}'] = _isNil(obj.{{field.name}}) ? [] : _map(obj.{{field.name}}, f => serialize{{field.type}}(f));
        {% else -%}
          if (unroll) json['{{field.name}}'] = _isNil(obj.{{field.name}}) ? null : serialize{{field.type}}(obj.{{field.name}});
        {% endif -%}
      {% elif field.type == 'Date | null' -%}
        {% if field.multi %}
          json['{{field.name}}'] = _isNil(obj.{{field.name}}) ? [] : _map(obj.{{field.name}}, d => d.toJSON());
        {% else -%}
          json['{{field.name}}'] = _isNil(obj.{{field.name}}) ? null : obj.{{field.name}}.toJSON();
        {% endif -%}
      {% else -%}
        json['{{field.name}}'] = obj.{{field.name}}
      {% endif -%}
    {% endif -%}
  {% endfor %}
{%- endmacro %}

{% macro auto_attributes(fields) -%}
  {% for field in fields -%}
    public {{field.name}}!: {{field.type}}{{ '[]' if field.multi }}
  {% endfor %}
{%- endmacro %}