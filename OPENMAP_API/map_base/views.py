from django.http import Http404
from django.shortcuts import render

import django_tables2 as tables

from map_base.models import Campaign, MapInput, MapOutput

def campaign_experiments(request, campaign_name):
    try:
        campaign = Campaign.objects.get(name=campaign_name)
    except Campaign.DoesNotExist:
        raise Http404("Campaign does not exist")

    map_inp = MapInput.objects.filter(for_map=campaign.for_map)
    map_out = MapOutput.objects.filter(for_map=campaign.for_map)
    keys = [ "experiment", ] + [inp.name for inp in map_inp] + [out.name for out in map_out]
    attr = [ tables.Column() for x in keys ]

    dyn_table = type('dyn_table', (tables.Table,), dict(zip(keys,attr)))

    data = []

    for experiment in campaign.experiments.all():
        vals = [ experiment.name, ] + [experiment.input_values.get(map_input=inp).value_request for inp in map_inp] + [experiment.output_values.get(map_output=out).value for out in map_out]
        data.append( dict(zip(keys,vals)) )

    return render(request, 'campaign_experiments.html', {'object_list': dyn_table(data)})
