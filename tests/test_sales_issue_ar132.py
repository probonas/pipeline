#!/usr/bin/env python3 -B
import unittest

from cromulent import vocab

from tests import TestSalesPipelineOutput, classification_sets


vocab.add_attribute_assignment_check()

class PIRModelingTest_AR132(TestSalesPipelineOutput):
    def test_modeling_ar132(self):
        '''
        AR-132: Add transaction types on to Sales provenance activity records
        '''
        output = self.run_pipeline('ar132')
        activies = output['model-activity']
        
        expected = {
            'tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:sales#PROV,B-A138,1774-05-30,0050' : 'Purchase',
            'tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:sales#PROV-MULTI,B-A111,1769-07-31,13,14' : 'Bought In'
        }

        expected_id = {
            'tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:sales#PROV,Br-4716,1837-03-11,0087' : 'http://vocab.getty.edu/aat/300445698', # passed has no label
            'tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:sales#PROV,B-A136,1773-07-20,0090' : 'https://data.getty.edu/local/thesaurus/unknown', #unknown has no label
        }

        for url,cl in expected.items():
            activity = activies[url]
            got = classification_sets(activity, classification_key='classified_as')
            self.assertIn(cl,got)

        for url,cl in expected_id.items():
            activity = activies[url]
            got = classification_sets(activity, key="id", classification_key='classified_as')
            self.assertIn(cl,got)
        


if __name__ == '__main__':
    unittest.main()
