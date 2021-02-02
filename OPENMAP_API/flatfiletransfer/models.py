from django.db import models
from os.path import splitext
from hashlib import sha256
from map_base.models import Campaign, Experiment

class ExpFileManager(models.Manager):
    def hashed_exp_filename(self, experiment, name_orig):
        try:
            exp_file = self.get(experiment=experiment, name_orig=name_orig)
        except ExpFile.DoesNotExist:
            filename, extension = splitext(name_orig)
            seed = "{}::{}::{}".format( experiment.campaign.name, experiment.name, filename )
            name_hash = "{}{}".format( sha256(seed.encode()).hexdigest(), extension )
            exp_file = ExpFile(experiment=experiment, name_orig=name_orig, name_hash=name_hash)
            exp_file.save()

        return exp_file

class ExpFile(models.Model):
    experiment = models.ForeignKey(Experiment, related_name = "files", on_delete=models.CASCADE)
    name_orig = models.CharField(max_length=255, null=False)
    name_hash = models.CharField(max_length=255, null=False)
    transfered = models.BooleanField(default=False)

    objects = ExpFileManager()

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['experiment','name_orig'], name='unique_exp_file_ref'),
                models.UniqueConstraint(fields=['name_hash'], name='unique_hash')
            ]

    def __str__(self):
        return "{}: {}: {}".format(self.experiment.campaign.name, self.experiment.name, self.name_orig)

class Metadata(models.Model):
    exp_file = models.ForeignKey(ExpFile, related_name = "metadata", on_delete=models.CASCADE)
    field = models.CharField(max_length=80, null=False)
    value = models.CharField(max_length=255, null=False)

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['exp_file', 'field'], name='unique_metadata_field_ref'),
            ]

    def __str__(self):
        return "{}: {}".format(self.exp_file.name_hash, self.field)
