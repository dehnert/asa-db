import datetime

from django.contrib.admin import SimpleListFilter

class TimePeriodFilter(SimpleListFilter):
    title = 'time period'
    parameter_name = 'time_period'

    def lookups(self, request, model_admin):
        return (
            ('past', 'Past', ),
            ('present', 'Current', ),
            ('future', 'Future', ),
        )

    def queryset(self, request, queryset):
        value = self.value()
        now = datetime.datetime.now()
        if value == None:
            return queryset
        elif value == 'past':
            dct = {
                '%s__lt' % (self.end_field, ): now,
            }
            return queryset.filter(**dct)
        elif value == 'present':
            dct = {
                '%s__lt' % (self.start_field, ): now,
                '%s__gt' % (self.end_field, ): now,
            }
            return queryset.filter(**dct)
        elif value == 'future':
            dct = {
                '%s__gt' % (self.start_field, ): now,
            }
            return queryset.filter(**dct)
        else:
            raise ValueError, "unknown period %s" % (value, )
