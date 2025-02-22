#!/usr/bin/env python3 -B
import unittest

from cromulent import vocab

from tests import TestPeoplePipelineOutput, classification_sets, classification_tree, classified_identifiers

vocab.add_attribute_assignment_check()

class PIRModelingTest_AR170(TestPeoplePipelineOutput):
    '''
    AR-170: Identify generic group records using the generic field name and populate profesional activity accordingly
    '''
    def test_modeling_ar170(self):
        output = self.run_pipeline('ar170')

        groups = output['model-groups']

        expected = {
            'tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:shared#GROUP,AUTH,Strubin' : {
                'label' : "Professional activity of \"Strubin\" from 18th to 19th century",
                'timespan' : ['1700-01-01T00:00:00Z', '1900-01-01T00:00:00Z']
            },
            'tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:shared#GROUP,AUTH,Tracy' : {
                'label' : "Professional activity of \"Tracy\" in the 18th century",
                'timespan' : ['1700-01-01T00:00:00Z', '1800-01-01T00:00:00Z']
            },
            'tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:shared#GROUP,AUTH,MYTENS' : {
                'label' : "Professional activity of \"Mytens\" from 17th to 18th century",
                'timespan' : ['1600-01-01T00:00:00Z', '1800-01-01T00:00:00Z']
            },
            'tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:shared#GROUP,AUTH,%5BANONYMOUS%20-%2014TH%20C.%5D' : {
                'label' : "Professional activity of Unknown persons in the 14th century",
                'timespan' : ['1300-01-01T00:00:00Z', '1400-01-01T00:00:00Z']
            },
            'tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:shared#GROUP,AUTH,RIEDEL%2C%20JOHANN' : {
                'label' : "Professional activity of \"Riedel, Johann\" in the 18th century",
                'timespan' : ['1700-01-01T00:00:00Z', '1800-01-01T00:00:00Z']
            },
            'tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:shared#GROUP,AUTH,ERTINGER' : {
                'label' : "Professional activity of \"Ertinger\" from 17th to 18th century",
                'timespan' : ['1600-01-01T00:00:00Z', '1800-01-01T00:00:00Z']
            },
            'tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:shared#GROUP,AUTH,%5BAMERICAN%20-%2019TH%20C.%5D' : {
                'label' : "Professional activity of American persons in the 19th century",
                'timespan' : ['1800-01-01T00:00:00Z', '1900-01-01T00:00:00Z']
            },
            'tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:shared#GROUP,AUTH,Alessandri%20family' : {
                'label' : "Professional activity of \"Alessandri Family\" from 14th to 20th century",
                'timespan' : ['1300-01-01T00:00:00Z', '2000-01-01T00:00:00Z']
            },
        }

        self.verify_results(groups, expected)

        professional_activities = groups['tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:shared#GROUP,AUTH,%5BETRUSCAN%5D']['carried_out'] if 'carried_out' in groups['tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:shared#GROUP,AUTH,%5BETRUSCAN%5D'] else []
        self.assertEqual(len(professional_activities), 1)
        # in the century active timespan is a BC date, do not produce any timespan related to the professional activity
        self.assertNotIn('timespan', professional_activities[0])

        # in case there is a nationality but no century active information, then no professional activity should be populated
        professional_activities = groups['tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:shared#GROUP,AUTH,%5BAMERICAN%5D']['carried_out'] if 'carried_out' in groups['tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:shared#GROUP,AUTH,%5BAMERICAN%5D'] else []
        self.assertEqual(len(professional_activities), 0)
        
        # check that when split, the all statement contents contain no empty nodes
        statements = [statement for statement in groups['tag:getty.edu,2019:digital:pipeline:REPLACE-WITH-UUID:shared#GROUP,AUTH,CERMAK']['referred_to_by'] ]
        for stmt in statements[1:]:
            self.assertIn('content',stmt)
            self.assertNotEqual(stmt['content'], '')
                
    def verify_results(self, groups, expected):
        for (key, value) in groups.items():
            if key in expected.keys():
                professional_activities = [a for a in value['carried_out'] if a['_label'].startswith('Professional activity')]
                self.assertEqual(len(professional_activities), 1)        
                self.assertEqual(professional_activities[0]['_label'], expected[key]['label'])
                # check that the timespan has a label, a type, an end of the begin and a begin of the end
                self.assertEqual(len(professional_activities[0]['timespan']), 4)
                self.assertEqual(professional_activities[0]['timespan']['end_of_the_begin'], expected[key]['timespan'][0])
                self.assertEqual(professional_activities[0]['timespan']['begin_of_the_end'], expected[key]['timespan'][1])

if __name__ == '__main__':
    unittest.main()