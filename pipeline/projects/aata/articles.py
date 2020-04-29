import pprint
import warnings

from bonobo.config import Configurable, Service, Option

from cromulent import model, vocab
from pipeline.util import _as_list
from pipeline.linkedart import \
			MakeLinkedArtAbstract, \
			MakeLinkedArtLinguisticObject, \
			MakeLinkedArtPerson, \
			get_crom_object, \
			add_crom_data

class ModelArticle(Configurable):
	helper = Option(required=True)
	language_code_map = Service('language_code_map')

	def model_record_desc_group(self, record, data):
		code = data['doc_type']['doc_code']
		cls = self.helper.document_type_class(code)
		record['object_type'] = cls

	def model_record_id_group(self, record, data):
		record.setdefault('identifiers', [])
		record.setdefault('part_of', [])

		rid = data['record_id']
		aata_ids = _as_list(data.get('aata_id'))
		cid = data.get('collective_rec_id')

		record['identifiers'] += [vocab.LocalNumber(ident='', content=aid) for aid in aata_ids]
		record['identifiers'] += [vocab.LocalNumber(ident='', content=rid)]

		if cid:
			uri = self.helper.article_uri(cid)
			parent = {'uri': uri}
			make_la_lo = MakeLinkedArtLinguisticObject()
			make_la_lo(parent)
			record['part_of'].append(parent)

	def model_authorship_group(self, record, data):
		if not data:
			return
		record.setdefault('_people', [])
# 		record.setdefault('_events', [])
		authors = _as_list(data.get('primary_author'))

		subevents = []
		mlap = MakeLinkedArtPerson()

		ordered_data = []
		article_label = record['label_string']
		creation_id = record['uri'] + '-Creation'
		creation = model.Creation(ident=creation_id, label=f'Creation of {article_label}')
		for a in authors:
			gaia_id = a['gaia_authority_id']
			gaia_type = a['gaia_authority_type']
			name = a['author_name']
			roles = _as_list(a['author_role'])
			order = a['author_order']

			ordered_data.append((order, name))

			identifiers = [self.helper.gci_number_id(gaia_id)]
			p = {
				'uri': self.helper.make_proj_uri(gaia_type, 'GAIA', gaia_id),
				'label': name,
				'name': name,
				'identifiers': identifiers,
			}

			mlap(p)
			record['_people'].append(p)

			for role in roles:
				part = model.Creation(ident='', label=f'{role} Creation sub-event')
				part.carried_out_by = get_crom_object(p)
				type = self.helper.role_type(role)
				if type:
					part.classified_as = type
				creation.part = part

		ordered_authors = [p[1] for p in sorted(ordered_data)]
		order_string = self.helper.ordered_author_string(ordered_authors)
		creation.referred_to_by = vocab.Note(ident='', content=order_string)
		record['created_by'] = creation

	def model_title_group(self, record, data):
		record.setdefault('identifiers', [])

		primary = data['primary']
		title = primary.get('title')
		translated = primary.get('title_translated')
		variants = _as_list(primary.get('title_variant'))

		if title:
			record['label'] = title
			record['identifiers'].append(vocab.PrimaryName(ident='', content=title))
		if translated:
			record['identifiers'].append(vocab.TranslatedTitle(ident='', content=translated))
		for v in variants:
			record['identifiers'].append(vocab.Title(ident='', content=v))

	def model_imprint_group(self, record, data):
		if not data:
			return
		record.setdefault('referred_to_by', [])
		record.setdefault('identifiers', [])

		edition = data.get('edition')
		series_number = data.get('series_number')
		doi = data.get('doi')
		coden = data.get('coden')
		website = data.get('website_address')
		publishers = _as_list(data.get('publisher'))
			# imprint_group/publisher/gaia_corp_id
			# imprint_group/publisher/publisher_location/gaia_geog_id
		distributors = _as_list(data.get('distributor'))
			# imprint_group/distributor/gaia_corp_id
			# imprint_group/distributor/distributor_location/gaia_geog_id
		journal = data.get('journal_info')
			# imprint_group/journal_info/aata_journal_id
			# imprint_group/journal_info/aata_issue_id
		degree = data.get('thesis_degree')
		tr = data.get('technical_report_number')

		if edition:
			record['referred_to_by'].append(vocab.EditionStatement(ident='', content=edition))

		if series_number:
			record['referred_to_by'].append(vocab.Note(ident='', content=series_number)) # TODO: classify this Note

		if doi:
			record['identifiers'].append(vocab.DoiIdentifier(ident='', content=doi))

		if website:
			record['referred_to_by'].append(vocab.Note(ident='', content=website))

		article_label = record['label_string']
		for publisher in publishers:
			corp_id = publisher.get('gaia_corp_id')
			geog_id = publisher.get('publisher_location', {}).get('gaia_geog_id')
			a = vocab.Publishing(ident='', label=f'Publishing of {article_label}')
			if corp_id:
				uri = self.helper.corporate_body_uri(corp_id)
				a.carried_out_by = model.Group(ident=uri)
			if geog_id:
				uri = self.helper.place_uri(geog_id)
				a.took_place_at = model.Place(ident=uri)

		for distributor in distributors:
			corp_id = publisher.get('gaia_corp_id')
			geog_id = publisher.get('distributor_location', {}).get('gaia_geog_id')
			a = vocab.Distributing(ident='', label=f'Distribution of {article_label}')
			if corp_id:
				uri = self.helper.corporate_body_uri(corp_id)
				a.carried_out_by = model.Group(ident=uri)
			if geog_id:
				uri = self.helper.place_uri(geog_id)
				a.took_place_at = model.Place(ident=uri)

		if journal:
			aata_id = journal.get('aata_journal_id')
			issue_id = journal.get('aata_issue_id')
			warnings.warn('TODO: handle journal link data')
			# aata_journal_id	Textual Work	part_of
			# aata_issue_id	Textual Work	(part_of)

		if degree:
			record['referred_to_by'].append(vocab.Note(ident='', content=degree))

		if tr:
			record['identifiers'].append(model.Identifier(ident='', content=tr)) # TODO: classify this Identifier

	def model_physical_desc_group(self, record, data):
		if not data:
			return
		record.setdefault('referred_to_by', [])

		pages = data.get('pages')
		collation = data.get('collation')
		illustrations = data.get('illustrations')
		medium = data.get('electronic_medium_type')

		if pages:
			record['referred_to_by'].append(vocab.PaginationStatement(ident='', content=pages))

		if collation:
			record['referred_to_by'].append(vocab.Description(ident='', content=collation))

		if illustrations:
			record['referred_to_by'].append(vocab.IllustruationStatement(ident='', content=illustrations))

		if medium:
			record['referred_to_by'].append(vocab.PhysicalStatement(ident='', content=medium))

	def model_notes_group(self, record, data):
		if not data:
			return
		record.setdefault('language', [])
		record.setdefault('identifiers', [])
		record.setdefault('referred_to_by', [])

		lang_docs = _as_list(data.get('lang_doc'))
		isbns = _as_list(data.get('isbn'))
		issns = _as_list(data.get('issn'))
		citation_note = data.get('citation_note')
		inotes = _as_list(data.get('internal_note'))

		for lang in lang_docs:
			l = self.helper.language_object_from_code(lang)
			if l:
				record['language'].append(l)

		for isbn in isbns:
			num = isbn.get('isbn_number')
			q = isbn.get('isbn_qualifier')
			if num:
				i = vocab.IsbnIdentifier(ident='', content=num)
				if q:
					i.referred_to_by = vocab.Note(ident='', content=q)
				record['identifiers'].append(i)

		for issn in issns:
			i = vocab.IssnIdentifier(ident='', content=issn)
			record['identifiers'].append(i)

		if citation_note:
			record['referred_to_by'].append(vocab.Citation(ident='', content=citation_note))

		for inote in inotes:
			record['referred_to_by'].append(vocab.Note(ident='', content=inote['note']))

	def model_abstract_group(self, record, data):
		if not data:
			return
		record.setdefault('referred_to_by', [])

		a = data.get('abstract')
		if a:
			record['referred_to_by'].append(vocab.Abstract(ident='', content=a))

	def model_classification_group(self, record, data):
		record.setdefault('classified_as', [])

		code = data['class_code']
		name = data['class_name']
		uri = self.helper.make_proj_uri('Classification', code)
		t = model.Type(ident=uri, label=name)
		record['classified_as'].append(t)

	def model_index_group(self, record, data):
		record.setdefault('about', [])

		opids = _as_list(data.get('other_persistent_id'))
		for opid in opids:
			eid = opid['external_id']
			uri = f'http://vocab.getty.edu/aat/{eid}'
			t = model.Type(ident=uri)
			record['about'].append(t)
		pass

	def model_article(self, data):
		make_la_lo = MakeLinkedArtLinguisticObject()
		make_la_lo(data)

		lo = get_crom_object(data)
		author = data.get('created_by')
		if author:
			lo.created_by = author

		for a in data.get('about', []):
			lo.about = a

		for c in data.get('classified_as', []):
			lo.classified_as = c

# 		print(factory.toString(get_crom_object(data), False))

	def __call__(self, data, language_code_map):
		'''
		Given an XML element representing an AATA record, extract information about the
		"article" (this might be a book, chapter, journal article, etc.) including:

		* document type
		* titles and title translations
		* organizations and their role (e.g. publisher)
		* creators and thier role (e.g. author, editor)
		* abstracts
		* languages

		This information is returned in a single `dict`.
		'''

		rid = data['record_id_group']['record_id']
		data['uri'] = self.helper.make_proj_uri('Article', rid)
		data['label'] = f'Article ({rid})' # this should get overridden in model_title_group
		data['label_string'] = f'Article ({rid})' # TODO: improve this

		self.model_title_group(data, data['title_group'])
		self.model_record_desc_group(data, data['record_desc_group'])
		self.model_record_id_group(data, data['record_id_group'])
		self.model_authorship_group(data, data.get('authorship_group'))
		self.model_imprint_group(data, data.get('imprint_group'))
		self.model_physical_desc_group(data, data.get('physical_desc_group'))
		self.model_notes_group(data, data.get('notes_group'))
		self.model_abstract_group(data, data.get('abstract_group'))
		for cg in _as_list(data.get('classification_group')):
			self.model_classification_group(data, cg)
		for ig in _as_list(data.get('index_group')):
			self.model_index_group(data, ig)
		self.model_article(data)

		return data
