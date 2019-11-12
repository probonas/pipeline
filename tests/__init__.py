import os
import os.path
import hashlib
import json
import uuid
import pprint
import unittest
from pathlib import Path

from cromulent import model, reader
from cromulent.model import factory
from pipeline.util import CromObjectMerger
from pipeline.projects.provenance import ProvenancePipeline
from pipeline.nodes.basic import Serializer, AddArchesModel

MODELS = {
	'Acquisition': 'model-acquisition',
	'Activity': 'model-activity',
	'Event': 'model-event',
	'Group': 'model-groups',
	'HumanMadeObject': 'model-object',
	'LinguisticObject': 'model-lo',
	'Person': 'model-person',
	'Place': 'model-place',
	'Procurement': 'model-activity',
	'Production': 'model-production',
	'Set': 'model-set',
	'VisualItem': 'model-visual-item'
}

class TestWriter():
	'''
	Deserialize the output of each resource and store in memory.
	Merge data for multiple serializations of the same resource.
	'''
	def __init__(self):
		self.output = {}
		self.merger = CromObjectMerger()
		super().__init__()

	def __call__(self, data: dict, *args, **kwargs):
		d = data['_OUTPUT']
		dr = data['_ARCHES_MODEL']
		if dr not in self.output:
			self.output[dr] = {}
		uu = data.get('uuid')
		if not uu and 'uri' in data:
			uu = hashlib.sha256(data['uri'].encode('utf-8')).hexdigest()
# 			print(f'*** No UUID in top-level resource. Using a hash of top-level URI: {uu}')
		if not uu:
			uu = str(uuid.uuid4())
# 			print(f'*** No UUID in top-level resource;')
# 			print(f'*** Using an assigned UUID filename for the content: {uu}')
		fn = '%s.json' % uu
		data = json.loads(d)
		if fn in self.output[dr]:
			r = reader.Reader()
			model_object = r.read(d)
			merger = self.merger
			content = self.output[dr][fn]
			try:
				m = r.read(content)
				if m == model_object:
					self.output[dr][fn] = data
					return
				else:
					merger.merge(m, model_object)
					self.output[dr][fn] = json.loads(factory.toString(m, False))
					return
			except model.DataError:
				print(f'Exception caught while merging data from {fn}:')
				print(d)
				print(content)
				raise
		else:
			self.output[dr][fn] = data

	def process_model(self, model):
		data = {v['id']: v for v in model.values()}
		return data

	def process_output(self, output):
		data = {k: self.process_model(v) for k, v in output.items()}
		return data

	def processed_output(self):
		return self.process_output(self.output)


def merge_lists(l, r):
	'''
	Given two lists `l` and `r`, return a generator of the combined items from both lists.

	If any two items l' in l and r' in r are both `dict`s and have the same value for the
	`id` key, they will be `merge`d and the resulting `dict` included in the results in
	place of l' or r'.
	'''
	identified = {}
	all_items = l + r
	other = []
	for item in all_items:
		try:
			item_id = item['id']
			if item_id in identified:
				identified[item_id] += [item]
			else:
				identified[item_id] = [item]
		except:
			other.append(item)

	for ident, items in identified.items():
		r = items[:]
		while len(r) > 1:
			a = r.pop(0)
			b = r.pop(0)
			m = merge(a, b)
			r.insert(0, m)
		yield from r

	yield from other

def merge(l, r):
	'''
	Given two items `l` and `r` of the same type, merge their contents and return the
	result. Raise an exception if `l` and `r` are of differing types.

	If the items are of type `dict`, recursively merge any values with shared keys, and
	also include data from any non-shared keys. If `l` and `r` both have values for the
	`id` key and they differ in value, raise an exception.

	If the items are of type `list`, merge them with `merge_lists`.

	If the items are of type `str` or `bytes`, return the value if `l` and `r` are equal.
	Otherwise raise and exception.
	'''
	if l is None:
		return r
	if r is None:
		return l

	if not isinstance(l, type(r)):
		pprint.pprint(l)
		pprint.pprint(r)
		raise Exception('bad data in json merge')

	if isinstance(l, dict):
		keys = set(list(l.keys()) + list(r.keys()))
		intersection = {k for k in keys if k in l and k in r}
		if 'id' in intersection:
			lid = l['id']
			rid = r['id']
			if lid != rid:
				pprint.pprint(l)
				pprint.pprint(r)
				raise Exception('attempt to merge two dicts with different ids: (%r, %r)' % (lid, rid))
		return {k: merge(l.get(k), r.get(k)) for k in keys}
	elif isinstance(l, list):
		return list(merge_lists(l, r))
	elif isinstance(l, (str, bytes)):
		if l == r:
			return l
		else:
			raise Exception('data conflict: %r <=> %r' % (l, r))
	else:
		raise NotImplementedError('unhandled type: %r' % (type(l)))
	return l


class ProvenanceTestPipeline(ProvenancePipeline):
	'''
	Test Provenance pipeline subclass that allows using a custom Writer.
	'''
	def __init__(self, writer, input_path, catalogs, auction_events, contents, **kwargs):
		super().__init__(input_path, catalogs, auction_events, contents, **kwargs)
		self.writer = writer

	def serializer_nodes_for_model(self, *args, model=None, **kwargs):
		nodes = []
		if model:
			nodes.append(AddArchesModel(model=model))
		nodes.append(Serializer(compact=False))
		nodes.append(self.writer)
		return nodes

	def get_services(self):
		services = super().get_services()
		services.update({
			'problematic_records': {},
			'location_codes': {}
		})
		return services


class TestProvenancePipelineOutput(unittest.TestCase):
	'''
	Parse test CSV data and run the Provenance pipeline with the in-memory TestWriter.
	Then verify that the serializations in the TestWriter object are what was expected.
	'''
	def setUp(self):
		self.catalogs = {
			'header_file': 'tests/data/pir/sales_catalogs_info_0.csv',
			'files_pattern': 'tests/data/pir/empty.csv',
		}
		self.contents = {
			'header_file': 'tests/data/pir/sales_contents_0.csv',
			'files_pattern': 'tests/data/pir/empty.csv',
		}
		self.auction_events = {
			'header_file': 'tests/data/pir/sales_descriptions_0.csv',
			'files_pattern': 'tests/data/pir/empty.csv',
		}
		os.environ['QUIET'] = '1'

	def tearDown(self):
		pass

	def run_pipeline(self, test_name):
		input_path = os.getcwd()
		catalogs = self.catalogs.copy()
		events = self.auction_events.copy()
		contents = self.contents.copy()
		
		tests_path = Path(f'tests/data/pir/{test_name}')
		catalog_files = list(tests_path.rglob('sales_catalogs_info*'))
		event_files = list(tests_path.rglob('sales_descriptions*'))
		content_files = list(tests_path.rglob('sales_contents*'))
		
		if catalog_files:
			catalogs['files_pattern'] = str(tests_path / 'sales_catalogs_info*')

		if event_files:
			events['files_pattern'] = str(tests_path / 'sales_descriptions*')

		if content_files:
			contents['files_pattern'] = str(tests_path / 'sales_contents*')
		
		writer = TestWriter()
		pipeline = ProvenanceTestPipeline(
				writer,
				input_path,
				catalogs=catalogs,
				auction_events=events,
				contents=contents,
				models=MODELS,
				limit=100,
				debug=True
		)
		pipeline.run()
		return writer.processed_output()
