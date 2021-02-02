from django.db import models

############################################################
#
############################################################
class MiscConfig(models.Model):
    name = models.CharField(max_length=80)
    value = models.CharField(max_length=255)

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['name'], name='unique_config_ref')
            ]

    def __str__(self):
        return self.name

############################################################
#
############################################################
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
    experiment_name = models.CharField(max_length=255, null=False)
    campaign_name = models.CharField(max_length=255, null=False)
    status = models.CharField(max_length=1, choices=EXP_STATUS_CHOICES, default='P')

    def __str__(self):
        return "{}: {} ({})".format(self.id, self.experiment_name, self.campaign_name)

############################################################
#
############################################################
class Module(models.Model):
    name = models.CharField(max_length=255, null=False)

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['name'], name='unique_module_ref')
            ]

    def __str__(self):
        return "{}".format(self.name)

############################################################
#
############################################################
class ExpModule(models.Model):
    MODULE_STATUS_CHOICES = [
                ("P", "Proposed"),
                ("Q", "Not Started"),
                ("R", "Running"),
                ("C", "Completed"),
                ("T", "Terminated Early"),
                ("H", "Suspended"),
            ]
    experiment = models.ForeignKey(Experiment, related_name='modules', on_delete=models.CASCADE)
    module = models.ForeignKey(Module, related_name='+', on_delete=models.CASCADE)
    status = models.CharField(max_length=1, choices=MODULE_STATUS_CHOICES, default='P')

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['experiment', 'module'], name='unique_expmodule_ref')
            ]

    def __str__(self):
        return "{} [{}]".format(self.module, self.experiment)

############################################################
#
############################################################
class ModuleInpVar(models.Model):
    module = models.ForeignKey(Module, related_name='inp_vars', on_delete=models.CASCADE)
    name = models.CharField(max_length=80, null=False)

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['name'], name='unique_moduleinp_ref')
            ]

    def __str__(self):
        return "{} ({})".format(self.name, self.module)

############################################################
#
############################################################
class ExpModuleInpVar(models.Model):
    exp_module = models.ForeignKey(ExpModule, related_name='inp_vars', on_delete=models.CASCADE)
    module_input = models.ForeignKey(ModuleInpVar, related_name='+', on_delete=models.CASCADE)
    input_value = models.FloatField(null=True)

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['exp_module','module_input'], name='unique_expmoduleinp_ref')
            ]

    def __str__(self):
        return "{} ({})".format(self.module_input.name, self.exp_module)

############################################################
#
############################################################
class ModuleOutVar(models.Model):
    module = models.ForeignKey(Module, related_name='out_vars', on_delete=models.CASCADE)
    name = models.CharField(max_length=80, null=False)
    inp_true = models.BooleanField(default=False)

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['name'], name='unique_moduleout_ref')
            ]

    def __str__(self):
        return "{} ({})".format(self.name, self.module)

############################################################
#
############################################################
class ExpOutVar(models.Model):
    experiment = models.ForeignKey(Experiment, related_name='out_vars', on_delete=models.CASCADE)
    module_output = models.ForeignKey(ModuleOutVar, related_name='+', on_delete=models.CASCADE)
    output_value = models.FloatField(null=True)

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['experiment','module_output'], name='unique_expout_ref')
            ]

    def __str__(self):
        return "{} [{}]".format(self.module_output.name, self.experiment)

    @property
    def name_value(self):
        return { '{}'.format(self.module_output.name): self.output_value }
