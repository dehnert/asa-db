import forms.models
from django.views.generic import list_detail
from django.shortcuts import render_to_response, get_object_or_404

import datetime

def fysm_by_years(request, year, category, ):
    if year is None: year = datetime.date.today().year
    queryset = forms.models.FYSM.objects.filter(year=year).order_by('group__name')
    category_obj = None
    if category != None:
        category_obj = get_object_or_404(forms.models.FYSMTag, slug=category)
        queryset = queryset.filter(tags=category_obj)
    categories = forms.models.FYSMTag.objects.all()
    return list_detail.object_list(
        request,
        queryset=queryset,
        template_name="forms/fysm_listing.html",
        template_object_name="fysm",
        extra_context={
            "year": year,
            "pagename": "fysm",
            "category": category_obj,
            "categories": categories,
        }
    )
