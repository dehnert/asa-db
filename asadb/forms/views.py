import forms.models
from django.views.generic import list_detail
from django.shortcuts import render_to_response, get_object_or_404

import datetime

def fysm_by_years(request, _, year):
    if year is None: year = datetime.date.today().year
    queryset = forms.models.FYSM.objects.filter(year=year).order_by('group__name')
    print queryset
    return list_detail.object_list(
        request,
        queryset=queryset,
        template_name="forms/fysm_listing.html",
        template_object_name="fysm",
        extra_context={
            "year": year,
            "pagename": "fysm",
        }
    )
