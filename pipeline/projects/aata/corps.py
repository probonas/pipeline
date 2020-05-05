import pprint
import warnings

from bonobo.config import Configurable, Service, Option

from cromulent import model, vocab
from pipeline.util import _as_list
from pipeline.linkedart import \
			MakeLinkedArtAbstract, \
			MakeLinkedArtLinguisticObject, \
			MakeLinkedArtOrganization, \
			MakeLinkedArtPerson, \
			MakeLinkedArtPlace, \
			get_crom_object, \
			add_crom_data

class ModelCorp(Configurable):
	helper = Option(required=True)

	def model_concept_group(self, record, data):
		record.setdefault('identifiers', [])
		record.setdefault('_places', []) # for extraction/serialization by the pipeline
		record.setdefault('places', []) # for pipeline.linkedart modeling code

		gaia_id = data['gaia_auth_id']
		snote = data.get('scope_note')
		inote = data.get('internal_note')
		snfnote = data.get('source_not_found_note')
		locations = _as_list(data.get('location', []))

		record['uri'] = self.helper.corporate_body_uri(gaia_id)
		record['identifiers'].append(self.helper.gci_number_id(gaia_id))

		if snote:
			record['referred_to_by'].append(vocab.Note(ident='', content=snote))
		if inote:
			record['referred_to_by'].append(vocab.InternalNote(ident='', content=inote))
		if snfnote:
			record['referred_to_by'].append(vocab.InternalNote(ident='', content=snfnote))

		mlap = MakeLinkedArtPlace()
		for loc in locations:
			geog_id = loc.get('gaia_geog_id')
			if geog_id:
				geog_uri = self.helper.place_uri(geog_id)
				geog_data = {
					'uri': geog_uri,
					'identifiers': [self.helper.gci_number_id(geog_id)],
				}
				geog_name = loc.get('location_string')
				if geog_name:
					geog_data['label'] = geog_name
					geog_data['name'] = geog_name
				mlap(geog_data)
				record['places'].append(geog_data)
				record['_places'].append(geog_data)

	def model_term_group(self, record, data):
		record.setdefault('identifiers', [])
		term_type = data['term_type']
		cl = model.Name
		if term_type == 'main':
			cl = vocab.PrimaryName
		name = data['corp_name']

		record.setdefault('label', name)
		record['identifiers'].append(cl(ident='', content=name))

	def model_place(self, data):
		mlao = MakeLinkedArtOrganization()
		mlao(data)

	def __call__(self, data):
		self.model_concept_group(data, data['concept_group'])
		for tg in _as_list(data.get('term_group')):
			self.model_term_group(data, tg)

		self.model_place(data)
		return data
