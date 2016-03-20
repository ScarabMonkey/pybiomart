import os
import pickle
import mock

import pytest
import pkg_resources

from .. import dataset

from .test_server import marts_request
from .test_mart import datasets_request, mart


@pytest.fixture
def dataset_(mart, datasets_request):
    """Returns a default dataset for testing."""

    with mock.patch.object(mart, 'get', return_value=datasets_request):
        return mart.datasets['mmusculus_gene_ensembl']


@pytest.fixture
def dataset_with_config(dataset_, config_request):
    """Returns default dataset with cached configuration."""

    with mock.patch.object(dataset_, 'get', return_value=config_request):
        dataset_.attributes
    return dataset_


@pytest.fixture
def config_request():
    """Loads cached configuration request."""

    # Dumped using the following code.
    # req = dataset.get(type='configuration', dataset=dataset_.name)
    # with open('config_request.pkl', 'wb') as file_:
    #    pickle.dump(req, file=file_, protocol=2)

    # Load cached request.
    rel_path = os.path.join('tests', 'data', 'config_request.pkl')
    file_path = pkg_resources.resource_filename(dataset.__name__, rel_path)

    with open(file_path, 'rb') as file_:
        return pickle.load(file_)


@pytest.fixture
def query_params():
    attributes = ['ensembl_gene_id']
    filters = {'chromosome_name': ['1']}
    return attributes, filters


@pytest.fixture
def query_request():
    """Loads cached query request."""

    # Dumped from inside query using the below code.
    # import pickle
    # with open('query_response.pkl', 'wb') as file_:
    #    pickle.dump(response, file=file_, protocol=2)

    # Load cached request.
    rel_path = os.path.join('tests', 'data', 'query_request.pkl')
    file_path = pkg_resources.resource_filename(dataset.__name__, rel_path)

    with open(file_path, 'rb') as file_:
        return pickle.load(file_)


class TestDataset(object):

    def test_attibutes(self, dataset_):
        """Tests basic attributes."""
        assert dataset_.name == 'mmusculus_gene_ensembl'
        assert dataset_.display_name == 'Mus musculus genes (GRCm38.p4)'

    def test_fetch_configuration(self, dataset_, config_request):
        """Tests fetching of filters/attributes."""

        with mock.patch.object(dataset_, 'get',
                               return_value=config_request) as mock_get:

            assert len(dataset_.filters) > 0
            assert len(dataset_.attributes) > 0

            mock_get.assert_called_once_with(type='configuration',
                                             dataset=dataset_.name)

    def test_fetch_attribute(self, dataset_, config_request):
        """Tests attributes of example attribute."""

        with mock.patch.object(dataset_, 'get', return_value=config_request):

            # Test example attribute.
            attr = dataset_.attributes['ensembl_gene_id']
            assert attr.name == 'ensembl_gene_id'
            assert attr.display_name == 'Ensembl Gene ID'
            assert attr.description == 'Ensembl Stable ID of the Gene'
            assert attr.default

    def test_fetch_filters(self, dataset_, config_request):
        """Tests attributes of example filter."""

        with mock.patch.object(dataset_, 'get', return_value=config_request):

            # Test example filter.
            filt = dataset_.filters['chromosome_name']
            assert filt.name == 'chromosome_name'
            assert filt.type == 'list'
            assert filt.description == ''

    def test_query(self, dataset_with_config, query_params, query_request):
        """Tests example query."""

        dataset_ = dataset_with_config

        with mock.patch.object(dataset_, 'get',
                               return_value=query_request) as mock_get:
            # Perform query.
            attributes, filters = query_params
            res = dataset_.query(attributes=attributes,
                                 filters=filters)

            # Check query result.
            assert len(res) > 0
            assert 'Ensembl Gene ID' in res

            # Check query xml.
            query = b"""<Query datasetConfigVersion="0.6" formatter="TSV"
 header="1" uniqueRows="1" virtualSchemaName="default">
<Dataset interface="default" name="mmusculus_gene_ensembl">
<Attribute name="ensembl_gene_id" />
<Filter name="chromosome_name" value="1" />
</Dataset></Query>"""
            query = b''.join(query.split(b'\n'))

            mock_get.assert_called_once_with(query=query)

    def test_query_attr_name(self, dataset_with_config,
                             query_params, query_request):
        """Tests example query, renaming columns to names."""

        dataset_ = dataset_with_config

        with mock.patch.object(dataset_, 'get',
                               return_value=query_request) as mock_get:
            # Perform query.
            attributes, filters = query_params
            res = dataset_.query(attributes=attributes,
                                 filters=filters, use_attr_names=True)

            # Check query result.
            assert len(res) > 0
            assert 'ensembl_gene_id' in res