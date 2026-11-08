"""Fetch only the tenant-scoped references a read needs, without traversing whole graphs."""
def reference_id(value):
    return getattr(value, 'id', value)


def hydrate(rows, organization, field, model, fields=('name',)):
    rows=list(rows)
    ids={reference_id(row._data.get(field)) for row in rows if row._data.get(field) is not None}
    missing={value for value in ids if value is not None}
    query=model.objects(organization=organization,id__in=list(missing))
    if fields is not None:query=query.only(*fields)
    lookup={doc.id:doc for doc in query} if missing else {}
    for row in rows:
        value=row._data.get(field)
        key=reference_id(value)
        if key in lookup:row._data[field]=lookup[key]
    return rows
