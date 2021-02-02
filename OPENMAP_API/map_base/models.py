from django.db import models
import re
from random import uniform as random_uniform

from map_base.util import generate_uid_node_campaign

############################################################
# MAP
############################################################
class MapBase(models.Model):
    name = models.CharField(max_length=255)
    storage_location = models.CharField(max_length=1024, blank=True, default='')
    storage_user = models.CharField(max_length=80, blank=True, default='')

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['name',], name='unique_map_ref')
            ]
        verbose_name = 'MAP base'

    def __str__(self):
        return "{}".format(self.name)

############################################################
# Facilities
############################################################
class MapFacility(models.Model):
    for_map = models.ForeignKey(MapBase, related_name='facilities', verbose_name='for MAP', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=1024)

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['for_map', 'name'], name='unique_facility_ref')
            ]
        verbose_name = 'MAP facility'
        verbose_name_plural = 'MAP facilities'

    def __str__(self):
        return "{}: {}".format(self.for_map, self.name)

############################################################
# Facilities
############################################################
class MLFacility(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=1024)
    train_script = models.CharField(max_length=255)
    probe_script = models.CharField(max_length=255)

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['name',], name='unique_ml_ref')
            ]
        verbose_name = 'ML facility'
        verbose_name_plural = 'ML facilities'

    def __str__(self):
        return "{}".format(self.name)

############################################################
# Campaign
############################################################
class Campaign(models.Model):
    ML_STATUS_CHOICES = [
                ("U", "Untrained"),
                ("O", "Out of date"),
                ("R", "Running training"),
                ("T", "Trained"),
                ("E", "Error during training"),
            ]
    for_map = models.ForeignKey(MapBase, related_name='campaigns', verbose_name='for MAP', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    max_experiments = models.PositiveIntegerField(default=0, blank=True)
    with_ml = models.ForeignKey(MLFacility, null=True, related_name='campaigns+', verbose_name='with ML', on_delete=models.SET_NULL)
    ml_model_status = models.CharField(max_length=1, choices=ML_STATUS_CHOICES, verbose_name='ML model status', default='U')
    goal = models.CharField(max_length=255, blank=True, default='')
    performance = models.FloatField(null=True, blank=True)
    uid_node = models.CharField(max_length=12, default=generate_uid_node_campaign, verbose_name='UID node')

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['for_map', 'name'], name='unique_campaign_ref'),
                models.UniqueConstraint(fields=['uid_node'], name='unique_campaign_mac_ref'),
            ]

    def propose_random_experiment(self):
        #if len( self.experiments.all() ) < max_experiments:
        experiment = Experiment.objects.new_proposed(self, 'random')

        for map_inp in MapInput.objects.filter(for_map=self.for_map):
            rndval = random_uniform(map_inp.min_val, map_inp.max_val)
            ExpInputVal.objects.create(experiment=experiment, map_input=map_inp, value_request=rndval)

        for map_stg in MapStage.objects.filter(for_map=self.for_map):
            ExpStage.objects.create(experiment=experiment, map_stage=map_stg)

        for map_out in MapOutput.objects.filter(for_map=self.for_map):
            ExpOutputVal.objects.create(experiment=experiment, map_output=map_out)

        return experiment

    def __str__(self):
        return "{}: {}".format(self.for_map, self.name)

############################################################
# Campaign Files
############################################################
class Campaign_File(models.Model):
    campaign = models.ForeignKey(Campaign, related_name='files', on_delete=models.CASCADE)
    file_type = models.CharField(max_length=80)
    file_location = models.CharField(max_length=1024)

    def __str__(self):
        return "{}: {}: {}".format(self.campaign, self.file_type, self.file_location)

############################################################
# Experiment
############################################################
class ExperimentManager(models.Manager):
    def new_proposed(self, campaign, mode):
        base_name = "Experiment - {}".format(mode)
        name_regex = "^{}\\s\\d+$".format(base_name)
        exclude_regex = "(?<={})\\s*\\d+".format(base_name)

        q = Experiment.objects.filter(campaign=campaign, name__iregex=name_regex)
        if (len(q)==0):
            name = "{} {}".format(base_name, 1)
        else:
            max_num = 0
            for exp_name in q.values_list('name', flat=True):
                num = int( re.search(exclude_regex, exp_name).group() )
                if (num > max_num):
                    max_num = num

            name = "{} {}".format(base_name, max_num+1)

        experiment = Experiment(campaign=campaign, name=name)
        experiment.save()
        return experiment

class Experiment(models.Model):
    EXP_STATUS_CHOICES = [
                ("P", "Proposed"),
                ("Q", "Not Started"),
                ("R", "Running"),
                ("C", "Completed"),
                ("T", "Terminated Early"),
                ("H", "Suspended"),
                ("X", "Hard Reject"),
                ("Z", "Soft Reject"),
            ]
    campaign = models.ForeignKey(Campaign, related_name = 'experiments', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=1, choices=EXP_STATUS_CHOICES, default='P')
    facility = models.ForeignKey(MapFacility, null=True, blank=True, related_name='experiments+', on_delete=models.SET_NULL) # related_name disabled by ending with '+'
    facility_expid = models.IntegerField(null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    objects = ExperimentManager()

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['campaign', 'name'], name='unique_exp_ref')
            ]

    def __str__(self):
        return "{}: {}".format(self.campaign, self.name)

############################################################
# Experiment Stage
############################################################
class MapStage(models.Model):
    for_map = models.ForeignKey(MapBase, related_name='stages', verbose_name='for MAP', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['for_map', 'name'], name='unique_mapstg_ref')
            ]
        verbose_name = 'MAP stage'

    def __str__(self):
        return "{}: {}".format(self.for_map, self.name)

class ExpStage(models.Model):
    STAGE_STATUS_CHOICES = [
                ("P", "Proposed"),
                ("Q", "Not Started"),
                ("R", "Running"),
                ("C", "Completed"),
                ("T", "Terminated Early"),
                ("H", "Suspended"),
            ]
    experiment = models.ForeignKey(Experiment, related_name = 'stages', on_delete=models.CASCADE)
    map_stage = models.ForeignKey(MapStage, related_name = '+', on_delete=models.CASCADE)
    status = models.CharField(max_length=1, choices=STAGE_STATUS_CHOICES, default='P')
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['experiment', 'map_stage'], name='unique_expstg_ref')
            ]

    def __str__(self):
        return "{}: {}".format(self.experiment, self.map_stage.name)

############################################################
# Inputs
############################################################
class MapInput(models.Model):
    for_map = models.ForeignKey(MapBase, related_name='inputs', verbose_name='for MAP', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    min_val = models.FloatField()
    max_val = models.FloatField()
    for_stage = models.ForeignKey(MapStage, related_name='inputs', null=True, blank=True, on_delete=models.SET_NULL)
    units = models.CharField(max_length=80, null=True, blank=True)

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['for_map', 'name'], name='unique_mapinp_ref')
            ]
        verbose_name = 'MAP input'

    def __str__(self):
        return "{}: {}".format(self.for_map, self.name)

class ExpInputVal(models.Model):
    experiment = models.ForeignKey(Experiment, related_name = 'input_values', on_delete=models.CASCADE)
    map_input = models.ForeignKey(MapInput, related_name = '+', on_delete=models.CASCADE)
    value_request = models.FloatField()
    value_actual = models.FloatField(null=True, blank=True)

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['experiment', 'map_input'], name='unique_expinpval_ref')
            ]

    def __str__(self):
        return "{}: {}".format(self.experiment, self.map_input.name)

############################################################
# Campaign Constraints on Inputs
############################################################
class CampaignConstraint(models.Model):
    campaign = models.ForeignKey(Campaign, related_name='constraints', on_delete=models.CASCADE)

class CampaignAtomicConstraint(models.Model):
    CAMPAIGN_CONSTRAINT_CHOICES = [
                ("BTW", "exclude between"),
                ("OUT", "exclude not between"),
                ("LTE", "exclude less than or equal to"),
                ("LT", "exclude less than"),
                ("GTE", "exclude greater than or equal to"),
                ("GT", "exclude greater than"),
                ("EQ", "exclude equal to"),
                ("NEQ", "exclude not equal to"),
            ]
    parent = models.ForeignKey(CampaignConstraint, related_name="sub_constraints", on_delete=models.CASCADE)
    parameter = models.ForeignKey(MapInput, related_name='+', on_delete=models.CASCADE)
    constraint_type = models.CharField(max_length=3, choices=CAMPAIGN_CONSTRAINT_CHOICES, default='BTW')
    v1 = models.FloatField()
    v2 = models.FloatField(null=True, blank=True)

############################################################
# Outputs
############################################################
class MapOutput(models.Model):
    for_map = models.ForeignKey(MapBase, related_name='outputs', verbose_name='for MAP', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    from_stage = models.ForeignKey(MapStage, related_name='outputs', null=True, blank=True, on_delete=models.SET_NULL)
    units = models.CharField(max_length=80, null=True, blank=True)

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['for_map', 'name'], name='unique_mapout_ref')
            ]
        verbose_name = 'MAP output'

    def __str__(self):
        return "{}: {}".format(self.for_map, self.name)

class ExpOutputVal(models.Model):
    experiment = models.ForeignKey(Experiment, related_name = 'output_values', on_delete=models.CASCADE)
    map_output = models.ForeignKey(MapOutput, related_name = '+', on_delete=models.CASCADE)
    value = models.FloatField(null=True, blank=True)

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['experiment', 'map_output'], name='unique_expoutval_ref')
            ]

    def __str__(self):
        return "{}: {}".format(self.experiment, self.map_output.name)

################################################################################
################################################################################
