from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from flatfiletransfer import views
from map_base.models import Campaign, Experiment
from map_base.tests import MapAPITestCase
from flatfiletransfer.models import ExpFile, Metadata

############################################################
#
# test requesting hashed name for files
#
############################################################
class FileHashesTests(MapAPITestCase):

    def setUp(self):
        MapAPITestCase.setUp(self)
        self.experiment = Experiment.objects.create( campaign=self.campaign, name=self.base_uid['experiment_name'] )

        self.uid_use = { 'campaign_name': self.base_uid['campaign_name'], 'experiment_name': self.base_uid['experiment_name'] }

    ##############################
    # POST
    ##############################
    def test_experiment_does_not_exist(self):
        url = reverse( views.file_hashes,
                kwargs = {'campaign_name': 'noCampaign', 'experiment_name': 'noExperiment'} )
        data = [ { "name_orig": "f1.dat" } ]

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_404_NOT_FOUND )

    def test_post_1_file(self):
        url = reverse( views.file_hashes, kwargs = self.uid_use )
        data = [ { "name_orig": "f1.dat" } ]

        response = self.client.post(url, data, format='json')
        self.assertContains( response, "name_hash", count=1 )

    def test_post_multi_file(self):
        url = reverse( views.file_hashes, kwargs = self.uid_use )
        data = [ { "name_orig": "f1.dat" }, {"name_orig": "f2.txt"}, {"name_orig": "f3.png"} ]

        response = self.client.post(url, data, format='json')
        self.assertContains( response, "name_hash", count=3 )

############################################################
#
# test reporting file transfer completion
#
############################################################
class FileTransferReportTests(MapAPITestCase):

    def setUp(self):
        MapAPITestCase.setUp(self)
        self.experiment = Experiment.objects.create( campaign=self.campaign, name=self.base_uid['experiment_name'] )

        self.uid_use = { 'campaign_name': self.base_uid['campaign_name'], 'experiment_name': self.base_uid['experiment_name'] }

        filenames = [ "f1.dat", "f2.txt", "f3.png" ]
        self.expfiles = [ ExpFile.objects.hashed_exp_filename(self.experiment, fn) for fn in filenames ]


    ##############################
    # PUT
    ##############################
    def test_hash_does_not_exist(self):
        url = reverse( views.file_transfer_report, kwargs = {'name_hash': 'noHash.dat'} )
        data = [ { "name_orig": "f1.dat" } ]

        response = self.client.put(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_404_NOT_FOUND )

    def test_hash_exists(self):
        url = reverse( views.file_transfer_report, kwargs = {'name_hash': self.expfiles[0].name_hash} )
        data = { "name_orig": self.expfiles[0].name_orig }

        response = self.client.put(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_200_OK )

############################################################
#
# test file-metadata actions
# (list/add metadata)
#
############################################################
class FileMetadataTests(MapAPITestCase):

    def setUp(self):
        MapAPITestCase.setUp(self)
        self.experiment = Experiment.objects.create( campaign=self.campaign, name=self.base_uid['experiment_name'] )

        filenames = [ "f1.dat", "f2.txt", "f3.png" ]
        self.expfiles = [ ExpFile.objects.hashed_exp_filename(self.experiment, fn) for fn in filenames ]

    ##############################
    # GET
    ##############################
    def test_get_hash_does_not_exist(self):
        url = reverse( views.file_metadata, kwargs = {'name_hash': 'noHash.dat'} )

        response = self.client.get(url, format='json')
        self.assertEqual( response.status_code, status.HTTP_404_NOT_FOUND )

    def test_get_empty_metadata(self):
        url = reverse( views.file_metadata, kwargs = {'name_hash': self.expfiles[0].name_hash} )

        response = self.client.get(url, format='json')
        self.assertEqual( response.status_code, status.HTTP_200_OK )
        self.assertEqual( response.data, [] )

    def test_get_metadata(self):
        url = reverse( views.file_metadata, kwargs = {'name_hash': self.expfiles[0].name_hash} )

        data = [ ("meta1", "data1"), ("meta2", "data2"), ("meta3", "data3") ]
        metadata = [ Metadata(exp_file=self.expfiles[0], field=x[0], value=x[1]).save() for x in data ]

        response = self.client.get(url, format='json')
        self.assertContains( response, "field", count=3 )
        self.assertContains( response, "value", count=3 )

    ##############################
    # POST
    ##############################
    def test_post_hash_does_not_exist(self):
        url = reverse( views.file_metadata, kwargs = {'name_hash': 'noHash.dat'} )

        data = {"field": "meta1", "value": "data1"}

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_404_NOT_FOUND )

    def test_post_single_metadata(self):
        url = reverse( views.file_metadata, kwargs = {'name_hash': self.expfiles[0].name_hash} )

        data = {"field": "meta1", "value": "data1"}

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_201_CREATED )

    def test_post_multiple_metadata(self):
        url = reverse( views.file_metadata, kwargs = {'name_hash': self.expfiles[0].name_hash} )

        data = [
                {"field": "meta1", "value": "data1"},
                {"field": "meta2", "value": "data2"},
                {"field": "meta3", "value": "data3"},
               ]

        for request_data in data:
            response = self.client.post(url, request_data, format='json')
            self.assertEqual( response.status_code, status.HTTP_201_CREATED )

            metadata = Metadata.objects.get(exp_file=self.expfiles[0], field=request_data['field'])
            self.assertEqual( metadata.value, request_data['value'] )

    def test_post_duplicate_metadata(self):
        url = reverse( views.file_metadata, kwargs = {'name_hash': self.expfiles[0].name_hash} )

        data = {"field": "meta1", "value": "data1"}

        old_metadata = Metadata(exp_file=self.expfiles[0], field=data['field'], value=data['value'])
        old_metadata.save()

        response = self.client.post(url, data, format='json')
        self.assertContains( response, "Error: metadata field already exists", status_code=status.HTTP_409_CONFLICT )

############################################################
#
# test file-metadata detail actions
# (retrieve, modify, delete individual metadata)
#
############################################################
class FileMetadataDetailTests(MapAPITestCase):
    def setUp(self):
        MapAPITestCase.setUp(self)
        self.experiment = Experiment.objects.create( campaign=self.campaign, name=self.base_uid['experiment_name'] )

        filename = "f1.dat"
        self.expfile = ExpFile.objects.hashed_exp_filename(self.experiment, filename)

        md = [ {"field": "meta1", "value": "data1"}, {"field": "meta2", "value": "data2"}, ]
        self.metadata = [ Metadata.objects.create(exp_file=self.expfile, field=x['field'], value=x['value']) for x in md ]

    ##############################
    # GET
    ##############################
    def test_get_md_does_not_exist(self):
        url = reverse( views.file_metadata_detail, kwargs = { 'name_hash': self.expfile.name_hash, 'field': 'noMeta' } )

        response = self.client.get( url, format='json')
        self.assertEqual( response.status_code, status.HTTP_404_NOT_FOUND )

    def test_get_md_exists(self):
        data = { 'field': 'meta1', 'value': 'data1' }
        url = reverse( views.file_metadata_detail, kwargs = { 'name_hash': self.expfile.name_hash, 'field': data['field'] } )

        response = self.client.get( url, format='json')
        self.assertContains( response, data['value'], count=1, status_code=status.HTTP_200_OK )

    ##############################
    # PUT
    ##############################
    def test_put_md_does_not_exist(self):
        url = reverse( views.file_metadata_detail, kwargs = { 'name_hash': self.expfile.name_hash, 'field': 'noMeta' } )

        request_data = {'value': 'morph1'}

        response = self.client.put( url, request_data, format='json')
        self.assertEqual( response.status_code, status.HTTP_404_NOT_FOUND )

    def test_put_md_modify_value(self):
        data = { 'field': 'meta1', 'value': 'data1' }
        url = reverse( views.file_metadata_detail, kwargs = { 'name_hash': self.expfile.name_hash, 'field': data['field'] } )

        self.assertEqual( self.metadata[0].field, data['field'] )
        self.assertEqual( self.metadata[0].value, data['value'] )

        request_data = {'field': 'meta1', 'value': 'morph1'}

        response = self.client.put( url, request_data, format='json')
        self.assertContains( response, request_data['value'], count=1, status_code=status.HTTP_200_OK )

        current_metadata = Metadata.objects.get(exp_file=self.expfile, field=data['field'])
        self.assertEqual( current_metadata.id, self.metadata[0].id )
        self.assertEqual( current_metadata.field, data['field'] )
        self.assertEqual( current_metadata.value, request_data['value'] )

    def test_put_md_modify_field_value(self):
        data = { 'field': 'meta1', 'value': 'data1' }
        url = reverse( views.file_metadata_detail, kwargs = { 'name_hash': self.expfile.name_hash, 'field': data['field'] } )

        self.assertEqual( self.metadata[0].field, data['field'] )
        self.assertEqual( self.metadata[0].value, data['value'] )

        request_data = {'field': 'ortho1', 'value': 'morph1'}

        response = self.client.put( url, request_data, format='json')
        self.assertContains( response, request_data['field'], count=1, status_code=status.HTTP_200_OK )
        self.assertContains( response, request_data['value'], count=1, status_code=status.HTTP_200_OK )

        current_metadata = Metadata.objects.get(exp_file=self.expfile, field=request_data['field'])
        self.assertEqual( current_metadata.id, self.metadata[0].id )
        self.assertEqual( current_metadata.field, request_data['field'] )
        self.assertEqual( current_metadata.value, request_data['value'] )

    def test_put_md_extra_junk(self):
        data = { 'field': 'meta1', 'value': 'data1' }
        url = reverse( views.file_metadata_detail, kwargs = { 'name_hash': self.expfile.name_hash, 'field': data['field'] } )

        self.assertEqual( self.metadata[0].field, data['field'] )
        self.assertEqual( self.metadata[0].value, data['value'] )

        request_data = {'field': 'meta1', 'value': 'morph1', 'junk': 'junk'}

        # expected behavior: ignore unrecognized
        response = self.client.put( url, request_data, format='json')
        self.assertContains( response, request_data['value'], count=1, status_code=status.HTTP_200_OK )

        current_metadata = Metadata.objects.get(exp_file=self.expfile, field=data['field'])
        self.assertEqual( current_metadata.id, self.metadata[0].id )
        self.assertEqual( current_metadata.field, data['field'] )
        self.assertEqual( current_metadata.value, request_data['value'] )

    def test_put_md_send_omit_field(self):
        data = { 'field': 'meta1', 'value': 'data1' }
        url = reverse( views.file_metadata_detail, kwargs = { 'name_hash': self.expfile.name_hash, 'field': data['field'] } )

        request_data = {'value': 'morph1'}

        # expected behavior: complain about missing field
        response = self.client.put( url, request_data, format='json')
        self.assertEqual( response.status_code, status.HTTP_400_BAD_REQUEST )

    def test_put_md_field_rename_collision(self):
        data = { 'field': 'meta1', 'value': 'data1' }
        url = reverse( views.file_metadata_detail, kwargs = { 'name_hash': self.expfile.name_hash, 'field': data['field'] } )

        self.assertEqual( self.metadata[0].field, data['field'] )
        self.assertEqual( self.metadata[0].value, data['value'] )

        request_data = {'field': 'meta2', 'value': 'morph1'}

        # expected behavior: fail due to database consistency
        response = self.client.put( url, request_data, format='json')
        self.assertEqual( response.status_code, status.HTTP_409_CONFLICT )

        current_metadata = Metadata.objects.get(exp_file=self.expfile, field=data['field'])
        self.assertEqual( current_metadata.id, self.metadata[0].id )
        self.assertEqual( current_metadata.field, data['field'] )
        self.assertEqual( current_metadata.value, data['value'] )

    ##############################
    # DELETE
    ##############################
    def test_delete_md_does_not_exist(self):
        url = reverse( views.file_metadata_detail, kwargs = { 'name_hash': self.expfile.name_hash, 'field': 'noMeta' } )

        response = self.client.delete( url, format='json')
        self.assertEqual( response.status_code, status.HTTP_404_NOT_FOUND )

    def test_delete_md_exists(self):
        data = { 'field': 'meta1', 'value': 'data1' }
        url = reverse( views.file_metadata_detail, kwargs = { 'name_hash': self.expfile.name_hash, 'field': data['field'] } )

        pre_count_metadata = Metadata.objects.filter(exp_file=self.expfile, field='meta1').count()
        self.assertEqual( pre_count_metadata, 1 )

        response = self.client.delete( url, format='json')
        self.assertEqual( response.status_code, status.HTTP_204_NO_CONTENT )

        post_count_metadata = Metadata.objects.filter(exp_file=self.expfile, field='meta1').count()
        self.assertEqual( post_count_metadata, 0 )
