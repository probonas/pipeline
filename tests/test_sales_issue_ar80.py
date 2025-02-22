#!/usr/bin/env python3 -B
import unittest

from cromulent import vocab

from tests import TestSalesPipelineOutput, classified_identifier_sets, classification_sets

vocab.add_attribute_assignment_check()

class PIRModelingTest_AR80(TestSalesPipelineOutput):
    def test_modeling_ar80(self):
        '''
        AR-80: Improve modeling of external links
        '''
        output = self.run_pipeline('ar80')
        texts = output['model-lo']
        
        record1 = texts['tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:sales#CATALOG,N-A13']
        record2 = texts['tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:sales#CATALOG,Br-A348']
        record3 = texts['tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:sales#CATALOG,D-A51']
        record4 = texts['tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:sales#CATALOG,SC-A38']
        record5 = texts['tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:sales#CATALOG,D-250']
        record6 =  texts['tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:sales#CATALOG,Br-A371']
        record7 = texts['tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:sales#CATALOG,N-A130']
        
        self.verifyReferences(record1, {
            'http://dx.doi.org/10.1163/2210-7886_ASC-162': {
            	'classification': 'Web Page',
            	'note': 'URL link to citation page hosted by ASCO/Brill. Citation page may have link to full pdf. '
            },      # art_sales_cats_online
            'http://archive.org/details/catalogusofnaaml01hoet': {
            	'classification': 'Web Page',
            	'note': 'URL link to citation page hosted by Internet Archive (some Dutch Hoet Sales). Full pdfs available via citation pages.'
            }       # link_to_PDF
        })

        self.verifyReferences(record2, {
            'http://artworld.york.ac.uk/': {
            	'classification': 'Web Page',
            	'note': 'URL link to York University. Goes to project page, no pdfs at all.'
            }       # art_world_in_britain
        })

        self.verifyReferences(record3, {
            'http://dx.doi.org/10.1163/2210-7886_ASC-1490': {
            	'classification': 'Web Page',
            	'note': 'URL link to citation page hosted by ASCO/Brill. Citation page may have link to full pdf. '
            },     # art_sales_cats_online
            'http://portal.getty.edu/books/inha_17892': {
            	'classification': 'Web Page',
            	'note': 'URL link to citation page hosted by Getty Research Portal. Full pdfs available via citation pages.'
        }          # portal_url_1
        })

        self.verifyReferences(record4, {
            'http://dx.doi.org/10.1163/2210-7886_ASC-3529': {
            	'classification': 'Web Page',
            	'note': 'URL link to citation page hosted by ASCO/Brill. Citation page may have link to full pdf. '
            }      # art_sales_cats_online
        })
        
        self.verifyReferences(record5, {
            'http://digi.ub.uni-heidelberg.de/diglit/creutzer1930_11_12': {
            	'classification': 'Web Page',
            	'note': 'URL link to citation page hosted by Heidelberg (20th C German Sales). Full pdfs available via citation pages.'
            }      # heidelberg_link
        })
        
        self.verifyReferences(record6, {
            'http://dx.doi.org/10.1163/2210-7886_ASC-553': {
            	'classification': 'Web Page',
            	'note': 'URL link to citation page hosted by ASCO/Brill. Citation page may have link to full pdf. '
            },      # art_sales_cats_online
            'http://artworld.york.ac.uk/': {
            	'classification': 'Web Page',
            	'note': 'URL link to York University. Goes to project page, no pdfs at all.'
            },       # art_world_in_britain
            'http://portal.getty.edu/books/inha_16953': {
            	'classification': 'Web Page',
            	'note': 'URL link to citation page hosted by Getty Research Portal. Full pdfs available via citation pages.'
            },      # portal url 1
            'http://portal.getty.edu/books/gri_9926529820001551': {
            	'classification': 'Web Page',
            	'note': 'URL link to citation page hosted by Getty Research Portal. Full pdfs available via citation pages.'
            },      # portal url 2
            'http://portal.getty.edu/books/pma_catalogueofcollec00cock': {
            	'classification': 'Web Page',
            	'note': 'URL link to citation page hosted by Getty Research Portal. Full pdfs available via citation pages.'
            },      # portal url 3
        })
        
        self.verifyReferences(record7, {
            'http://dx.doi.org/10.1163/2210-7886_ASC-453': {
            	'classification': 'Web Page',
            	'note': 'URL link to citation page hosted by ASCO/Brill. Citation page may have link to full pdf. '
            },      # art_sales_cats_online
            'http://archive.org/details/catalogusofnaaml01hoet': {
            	'classification': 'Web Page',
            	'note': 'URL link to citation page hosted by Internet Archive (some Dutch Hoet Sales). Full pdfs available via citation pages.'
            },       # link_to_PDF
            'http://portal.getty.edu/books/inha_16901': {
            	'classification': 'Web Page',
            	'note': 'URL link to citation page hosted by Getty Research Portal. Full pdfs available via citation pages.'
            },      # portal url 1
            'http://portal.getty.edu/books/inha_16900': {
            	'classification': 'Web Page',
            	'note': 'URL link to citation page hosted by Getty Research Portal. Full pdfs available via citation pages.'
            }      # portal url 2
        })

    def verifyReferences(self, record, expectedUrlsDict):
        expectedUrls = expectedUrlsDict.keys()
        self.assertIn('referred_to_by', record)
        
        refs = [ref for ref in record['referred_to_by'] if 'access_point' in ref]
        self.assertEqual(len(refs), len(expectedUrls))
        
        got = {}
        import pprint
        for r in refs:
            reftype = r['type']
            # import pdb; pdb.set_trace()
            self.assertEqual(len(r['access_point']), 1)
            url = r['access_point'][0]['id']
            got[url] = {
                'type': reftype,
                'refs': classified_identifier_sets(r, 'referred_to_by'),
                'classification': classification_sets(r)
            }
        
        for url, expected in expectedUrlsDict.items():
            gotData = got[url]
            if 'note' in expected:
                self.assertIn(expected['note'], gotData['refs']['Note'])
            if 'classification' in expected:
                self.assertIn(expected['classification'], gotData['classification'])

        for url in expectedUrls:
            ref = [ref for ref in refs if 'id' in ref['access_point'][0] and ref['access_point'][0]['id'] == url]
            self.assertEqual(len(ref), 1)
            ref = ref[0]
            self.assertEqual(ref['type'], 'DigitalObject')


if __name__ == '__main__':
    unittest.main()
