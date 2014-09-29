from collections import namedtuple


def make_enum(*values, **kwargs):
    names = kwargs.get('names')
    if names:
        return namedtuple('Enum', names)(*values)
    return namedtuple('Enum', values)(*values)


ACTION_LOG_STATUSES = make_enum(
    'added',
    'existed',
    'failed'
)
