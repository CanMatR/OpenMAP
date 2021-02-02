from rest_framework import serializers
from surrogate_base.models import Module, ModuleInpVar
from surrogate_base.models import Experiment, ExpModule, ExpModuleInpVar

############################################################
#
############################################################
class IdSerializer(serializers.Serializer):
    id = serializers.IntegerField()

############################################################
#
############################################################
class NewExperimentSerializer(serializers.Serializer):
    experiment_name = serializers.CharField(max_length=255)
    campaign_name = serializers.CharField(max_length=255)

    def create(self, validated_data):
        experiment = Experiment.objects.create(
                            experiment_name=validated_data.get('experiment_name'),
                            campaign_name=validated_data.get('campaign_name')
                        )
        # additionally setup modules for experiment
        all_modules = Module.objects.all()
        for module in all_modules:
            exp_module = ExpModule.objects.create(experiment=experiment, module=module)

        return experiment

############################################################
#
############################################################
class ModuleConfigSerializer(serializers.Serializer):
    input_name = serializers.CharField(source='module_input.name')
    input_value = serializers.FloatField(allow_null=True)

    def validate_input_name(self, name):
        try:
            module = self.context.get('exp_module').module
            module_input = ModuleInpVar.objects.get(module=module, name=name)
        except ModuleInpVar.DoesNotExist:
            message = "'{}' is not a known input for {}".format(name, self.context.get('exp_module').module.name)
            raise serializers.ValidationError(message)

        return name

    def create(self, validated_data):
        exp_module = self.context.get('exp_module')
        module_input = ModuleInpVar.objects.get(name=validated_data.get('module_input')['name'])
        exp_inp = ExpModuleInpVar.objects.create(
                                exp_module=exp_module,
                                module_input=module_input,
                                input_value=validated_data.get('input_value')
                            )

############################################################
#
############################################################
class StatusSerializer(serializers.Serializer):
    status = serializers.CharField(max_length=1)

############################################################
#
############################################################
class OutputSerializer(serializers.Serializer):
    name_value = serializers.DictField(child=serializers.FloatField())
