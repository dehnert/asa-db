from django.db.models import Q

from django_filters.filters import Filter, NumberFilter

class MultiFilter(Filter):
    def __init__(self, names, *args, **kwargs):
        super(MultiFilter, self).__init__(self, *args, **kwargs)
        assert len(names) > 0
        self.names = names

    def initial_q(self, value):
        return Q()

    def filter(self, qs, value):
        if not value:
            return qs
        if isinstance(value, (list, tuple)):
            lookup = str(value[1])
            if not lookup:
                lookup = 'exact' # we fallback to exact if no choice for lookup is provided
            value = value[0]
        else:
            lookup = self.lookup_type
        if value:
            q = self.initial_q(value)
            for name in self.names:
                q = q | Q(**{'%s__%s' % (name, lookup): value})
            qs = qs.filter(q)
        return qs

class MultiNumberFilter(MultiFilter,NumberFilter):
    pass
