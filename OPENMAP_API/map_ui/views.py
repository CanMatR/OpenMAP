from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms import formset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from map_base.models import MapBase, Campaign, Experiment, ExpStage, ExpInputVal, ExpOutputVal
from map_base.models import MapInput, MapStage, MapOutput
from map_ui.forms import CampaignForm
from map_ui.forms import ExperimentForm, ExpInputForm, BaseInputFormSet
from map_ui.tables import CampaignExperimentsTable
from map_ui.tables import ExperimentInputsTable, ExperimentOutputsTable

import map_base.tasks as celery_task

############################################################
#
# map_index
#
# list of maps
#
############################################################
@login_required
def map_index(request):
    map_list = MapBase.objects.all()
    context = {
                'map_list': map_list,
            }

    return render(request, 'map_ui/index.html', context)

############################################################
#
# campaign_index
#
# list of campaigns
#
############################################################
@login_required
def campaign_index(request, map_name):

    for_map = get_object_or_404(MapBase, name=map_name)
    campaign_list = Campaign.objects.filter(for_map=for_map)
    context = {
                'for_map': for_map,
                'campaign_list': campaign_list,
            }

    return render(request, 'campaign/index.html', context)

############################################################
#
# campaign_detail
#
# campaign settings
# list of experiments belonging to campaign
#
############################################################
@login_required
def campaign_detail(request, campaign_name):

    campaign = get_object_or_404(Campaign, name=campaign_name)

    if request.method == 'POST':
        if 'save_campaign' in request.POST:
            form = CampaignForm(request.POST, instance=campaign, prefix='campaign')
            form.fields['for_map'].disabled = True
            if form.is_valid():
                campaign = form.save(commit=False)
                if 'with_ml' in form.changed_data:
                    # if changing ML system, safest to assume untrained
                    # consider probing status as alternative
                    campaign.ml_model_status = 'U'
                campaign.save()

                return HttpResponseRedirect(
                        reverse( 'ui:campaign_detail',
                                kwargs = {'campaign_name': campaign.name} )
                        )
        elif 'run_campaign' in request.POST:
            form = CampaignForm(request.POST, instance=campaign, prefix='campaign')
            form.fields['for_map'].disabled = True
            if form.is_valid():
                campaign = form.save()
                if 'with_ml' in form.changed_data:
                    # if changing ML system, safest to assume untrained
                    # consider probing status as alternative
                    campaign.ml_model_status = 'U'
                campaign.save()

                n_experiment = len(campaign.experiments.all()) # consider filtering by status to exclude failed/cancelled experiments
                if ( n_experiment > 0 ):

                    if ( campaign.ml_model_status == "U" ):
                        # ML model hasn't been trained on all available data - updating model will lead to probing if not at max experiments
                        transaction.on_commit( lambda: celery_task.update_model.apply_async( (campaign.name,) ) )

                    elif ( campaign.ml_model_status == "O" ):
                        # ML model hasn't been trained on all available data - updating model will lead to probing if not at max experiments
                        transaction.on_commit( lambda: celery_task.update_model.apply_async( (campaign.name,) ) )

                    elif ( campaign.ml_model_status == "R" ):
                        # ML model is being trained - consider triggering a check to see if there are any problems
                        pass

                    elif ( campaign.ml_model_status == "T" ):
                        # ML model is trained - probe to generate a new experiment
                        if ( n_experiment < campaign.max_experiments ):
                            transaction.on_commit( lambda: celery_task.probe_model.apply_async( (campaign.name,) ) )

                    elif ( campaign.ml_model_status == "E" ):
                        # ML model error reported - appropriate handling TBD
                        pass
                else:
                    # generate random experiment
                    if campaign.max_experiments > 0:
                        experiment = campaign.propose_random_experiment()
                        transaction.on_commit( lambda: celery_task.place_experiment.delay(campaign_name, experiment.name) )
                
                return HttpResponseRedirect(
                        reverse( 'ui:campaign_detail',
                                kwargs = {'campaign_name': form.cleaned_data['name']} )
                        )

        elif "propose_random" in request.POST:
            experiment = campaign.propose_random_experiment()
            transaction.on_commit( lambda: celery_task.place_experiment.delay(campaign_name, experiment.name) )

            form = CampaignForm(instance=campaign, prefix='campaign')

    else:
        form = CampaignForm(instance=campaign, prefix='campaign')

    form.fields['for_map'].disabled = True

    experiment_list = CampaignExperimentsTable(campaign.experiments.all())

    context = {
                'campaign': campaign,
                'form': form,
                'experiment_list': experiment_list,
            }

    return render(request, 'campaign/detail.html', context)

############################################################
#
# campaign_new
#
# create new campaign
#
############################################################
@login_required
def campaign_new(request):

    if request.method == 'POST':
        form = CampaignForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(
                    reverse( 'ui:campaign_detail',
                            kwargs = {'campaign_name': form.cleaned_data['name']} )
                    )
    else:
        form = CampaignForm()

    context = {
                'form': form,
            }

    return render(request, 'campaign/new.html', context)

@login_required
def campaign_new_for_map(request, map_name):

    for_map = get_object_or_404(MapBase, name=map_name)

    if request.method == 'POST':
        form = CampaignForm(request.POST, initial={'for_map': for_map})
        form.fields['for_map'].disabled = True
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(
                    reverse( 'ui:campaign_detail',
                            kwargs = {'campaign_name': form.cleaned_data['name']} )
                    )
    else:
        form = CampaignForm(initial={'for_map': for_map})
        form.fields['for_map'].disabled = True

    context = {
                'for_map': for_map,
                'form': form,
            }

    return render(request, 'campaign/new.html', context)

@login_required
def propose_user_experiment(request, campaign_name):
    campaign = get_object_or_404(Campaign, name=campaign_name)
    map_inps = MapInput.objects.filter(for_map=campaign.for_map)

    if request.method == 'POST':
        exp_form = ExperimentForm(request.POST, prefix='experiment')
        if len(map_inps) > 0:
            InputFormset = formset_factory(ExpInputForm, formset=BaseInputFormSet, max_num=len(map_inps))
            inp_forms = InputFormset(request.POST, prefix='expinp')

            if exp_form.is_valid() and inp_forms.is_valid():
                experiment = Experiment.objects.new_proposed(campaign=campaign, mode=exp_form.cleaned_data['label'])

                for inp_form in inp_forms.forms:
                    map_input = MapInput.objects.get(for_map=campaign.for_map, name=inp_form.cleaned_data['input_name'])
                    ExpInputVal.objects.create(experiment=experiment, map_input=map_input, value_request=inp_form.cleaned_data['input_value'])

                map_stages = MapStage.objects.filter(for_map=campaign.for_map)
                for map_stg in map_stages:
                    new_exp_stg = ExpStage.objects.create(experiment=experiment, map_stage=map_stg)

                map_outputs = MapOutput.objects.filter(for_map=campaign.for_map)
                for map_out in map_outputs:
                    new_exp_out = ExpOutputVal.objects.create(experiment=experiment, map_output=map_out)

                transaction.on_commit( lambda: celery_task.place_experiment.delay(campaign_name, experiment.name) )

                return HttpResponseRedirect( reverse( 'ui:campaign_detail', kwargs = {'campaign_name': campaign_name} ) )

            context = {
                        'campaign': campaign,
                        'exp_form': exp_form,
                        'inp_forms': inp_forms,
                    }
        else:
            # experiment doesn't take inputs
            if exp_form.is_valid():
                experiment = Experiment.objects.new_proposed(campaign=campaign, mode=exp_form.cleaned_data['label'])

                map_stages = MapStage.objects.filter(for_map=campaign.for_map)
                for map_stg in map_stages:
                    new_exp_stg = ExpStage.objects.create(experiment=experiment, map_stage=map_stg)

                map_outputs = MapOutput.objects.filter(for_map=campaign.for_map)
                for map_out in map_outputs:
                    new_exp_out = ExpOutVal.objects.create(experiment=experiment, map_output=map_out)

                transaction.on_commit( lambda: celery_task.place_experiment.delay(campaign_name, experiment.name) )

                return HttpResponseRedirect( reverse( 'ui:campaign_detail', kwargs = {'campaign_name': campaign_name} ) )

            context = {
                        'campaign': campaign,
                        'exp_form': exp_form,
                    }
    else:
        exp_form = ExperimentForm(initial={'label': 'user'}, prefix='experiment')

        if len(map_inps) > 0:
            InpInit = [ { 'campaign_name': campaign_name, 'input_name': x.name } for x in map_inps ]

            InputFormset = formset_factory(ExpInputForm, formset=BaseInputFormSet, max_num=len(map_inps))
            inp_forms = InputFormset(initial=InpInit, prefix='expinp')

            context = {
                        'campaign': campaign,
                        'exp_form': exp_form,
                        'inp_forms': inp_forms,
                    }
        else:
            context = {
                        'campaign': campaign,
                        'exp_form': exp_form,
                    }

    return render(request, 'experiment/user_propose.html', context)

############################################################
#
# experiment_detail
#
# information about experiment
# list of inputs and outputs
#
############################################################
@login_required
def experiment_detail(request, campaign_name, experiment_name):

    experiment = get_object_or_404(Experiment, campaign__name=campaign_name, name=experiment_name)

    inputs_list = ExperimentInputsTable( experiment.input_values.all() )
    outputs_list = ExperimentOutputsTable( experiment.output_values.all() )

    context = {
                'experiment': experiment,
                'inputs_list': inputs_list,
                'outputs_list': outputs_list,
            }

    return render(request, 'experiment/detail.html', context)
