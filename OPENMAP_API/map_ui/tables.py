from django_tables2 import tables, columns, A

from map_base.models import Experiment

class CampaignExperimentsTable(tables.Table):
    name = columns.Column( linkify=("ui:experiment_detail", {"campaign_name": A("campaign__name"), "experiment_name": A("name")}) )
    facility = columns.Column()
    status = columns.Column()
    start_time = columns.DateTimeColumn()
    end_time = columns.DateTimeColumn()

    class Meta:
        attrs = {"class": "paleblue"}

    def render_facility(self, value):
        return "{}".format( value.name )

class ExperimentInputsTable(tables.Table):
    map_input = columns.Column(verbose_name="Name")
    value_request = columns.Column(verbose_name="Requested Value")
    value_actual = columns.Column(verbose_name="Actual Value")

    class Meta:
        attrs = {"class": "paleblue"}

    def render_map_input(self, value):
        return "{}".format( value.name )

class ExperimentOutputsTable(tables.Table):
    map_output = columns.Column(verbose_name="Name")
    value = columns.Column(verbose_name="Value")

    class Meta:
        attrs = {"class": "paleblue"}

    def render_map_output(self, value):
        return "{}".format( value.name )
