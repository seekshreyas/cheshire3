u"""Cheshire3 DocumentFactory Unittests.

DocumentFactory configurations may be customized by the user. For the purposes 
of unittesting, configuration files will be ignored and DocumentFactory 
instances will be instantiated using configuration data defined within this 
testing module, and tests carried out on instances.
"""

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import re    
import string

from lxml import etree

from cheshire3.documentFactory import SimpleDocumentFactory, \
ComponentDocumentFactory
from cheshire3.record import LxmlRecord
from cheshire3.test.testConfigParser import Cheshire3ObjectTestCase


class DocumentFactoryTestCase(Cheshire3ObjectTestCase):
    
    def _get_testData(self):
        return []

    def test_load(self):
        # Test that load method of an instance returns the instance
        for args in self._get_testData():
            thing = self.testObj.load(self.session, *args)
            self.assertIsInstance(thing, self._get_class())


class SimpleDocumentFactoryTestCase(DocumentFactoryTestCase):
    """Cheshire3 SimpleDocumentFactory Test Case."""
    
    @classmethod
    def _get_class(self):
        return SimpleDocumentFactory
    
    def _get_config(self):
        return etree.XML('''\
<subConfig type="documentFactory" id="baseDocumentFactory">
    <objectType>cheshire3.documentFactory.{0}</objectType>
</subConfig>'''.format(self._get_class().__name__))
        

class ComponentDocumentFactoryTestCase(DocumentFactoryTestCase):
    """ComponentDocumentFactory Test Case with simple XPath selectors."""
    
    @classmethod
    def _get_class(self):
        return ComponentDocumentFactory
    
    def _get_config(self):
        # Return a parsed config for the object to be tested
        return etree.XML('''\
<subConfig type="documentFactory" id="{0}">
    <objectType>cheshire3.documentFactory.{0}</objectType>
    <source>
      <xpath>meal</xpath>
    </source>
    <options>
        <default type="cache">0</default>
        <default type="format">component</default>
    </options>
</subConfig>'''.format(self._get_class().__name__))
        
    def _get_testData(self):
        yield (LxmlRecord(etree.XML("""
        <menu>
            <meal>
                <egg/>
                <bacon/>
            </meal>
            <meal>
                <egg/>
                <sausage/>
                <bacon/>
            </meal>
            <meal>
                <egg/>
                <spam/>
            </meal>
            <meal>
                <egg/>
                <bacon/>
                <spam/>
            </meal>
        </menu>
        """)),)
    
    def _get_testDataAndExpected(self):
        for args in self._get_testData():
            rec = args[0]
            yield (rec,
                   ["""(?L)^<c3:?component.*?>{0}</c3:?component>$""".format(
                                                             etree.tostring(el)
                                                             )
                    for el in
                    rec.process_xpath(self.session, 'meal')]
                   )

    def test_componentExtraction(self):
        i = 0
        for rec, expectedDocs in self._get_testDataAndExpected():
            rec.id = format(i, "d>0")
            i += 1 
            self.testObj.load(self.session, rec)
            docs = []
            for doc in self.testObj:
                docs.append(doc)
            # Check expected number of Documents generated
            self.assertEqual(len(expectedDocs),
                             len(docs),
                             "Number of docs ({0}) not as expected"
                             " ({1}) when loading {2!r}".format(
                                                          len(docs),
                                                          len(expectedDocs),
                                                          rec
                                                       )
                             )
            for doc, expected in zip(docs, expectedDocs):
                docstr = doc.get_raw(self.session)
                self.assertRegexpMatches(docstr, expected)
    

class SpanComponentDocumentFactoryTestCase(ComponentDocumentFactoryTestCase):
    """ComponentDocumentFactory Test Case with SpanXPathSelectors."""
    
    def _get_dependencyConfigs(self):
        yield etree.XML('''
        <subConfig type="selector" id="spanXPath">
            <objectType>cheshire3.selector.SpanXPathSelector</objectType>
            <source>
                <xpath>hr</xpath>
                <xpath>hr</xpath>
            </source>
        </subConfig>''')

    def _get_config(self):
        # Return a parsed config for the object to be tested
        return etree.XML('''
        <subConfig type="documentFactory" id="componentDocumentFactory">
          <objectType>
            cheshire3.documentFactory.ComponentDocumentFactory
          </objectType>
          <source>
            <xpath ref="spanXPath" />
          </source>
          <options>
            <setting type="keepStart">0</setting>
            <setting type="keepEnd">0</setting>
            <default type="cache">0</default>
            <default type="format">component</default>
            <default type="codec">utf-8</default>
          </options>
        </subConfig>''')

    def _get_testDataAndExpected(self):
        # Simple example
        yield (LxmlRecord(etree.XML("""
            <div>
                <hr/>
                <p>
                    Some text.
                </p>
                <hr/>
            </div>""")),
            [re.compile("""^<c3:?component.*?>
                <p>
                    Some text.
                </p>
                </c3:?component>$""", re.LOCALE)])
        # Simple example with tail text
        yield (LxmlRecord(etree.XML("""
            <div>
                <hr/>
                <p>
                    Some text.
                </p> With tail text.
                <hr/>
            </div>""")),
            [re.compile("""^<c3:?component.*?>
                <p>
                    Some text.
                </p> With tail text.
                </c3:?component>$""", re.LOCALE)])
        # Example where endNode is not a sibling of startNode
        # Tail text should be excluded now
        yield (LxmlRecord(etree.XML("""
            <div>
                <hr/>
                <p>
                    Some text.
                    <hr/>
                </p> With tail text.
            </div>""")),
            [re.compile("""^<c3:?component.*?>
                <p>
                    Some text.
                    </p></c3:?component>$""", re.LOCALE)])
        # Example where endNode is sibling of startNode ancestor
        yield (LxmlRecord(etree.XML("""
            <div>
                <p>Some text.
                    <hr/>
                </p> With tail text
                <hr/>
            </div>""")),
           [re.compile("""^<c3:?component.*?><p>
                </p> With tail text
                </c3:?component>$""", re.LOCALE)])


class KSSpanComponentDocumentFactoryTestCase(SpanComponentDocumentFactoryTestCase):
    "ComponentDocumentFactory Test Case with SpanXPathSelectors + keepStart."
    
    def _get_config(self):
        # Return a parsed config for the object to be tested
        return etree.XML('''
        <subConfig type="documentFactory" id="componentDocumentFactory">
          <objectType>
            cheshire3.documentFactory.ComponentDocumentFactory
          </objectType>
          <source>
            <xpath ref="spanXPath" />
          </source>
          <options>
            <setting type="keepStart">1</setting>
            <setting type="keepEnd">0</setting>
            <default type="cache">0</default>
            <default type="format">component</default>
            <default type="codec">utf-8</default>
          </options>
        </subConfig>''')

    def _get_testDataAndExpected(self):
        # Simple example
        yield (LxmlRecord(etree.XML("""
            <div>
                <hr/>
                <p>
                    Some text.
                </p>
                <hr/>
            </div>""")),
            [re.compile("""^<c3:?component.*?><hr></hr>
                <p>
                    Some text.
                </p>
                </c3:?component>$""", re.LOCALE)])
        # Simple example with tail text
        yield (LxmlRecord(etree.XML("""
            <div>
                <hr/>
                <p>
                    Some text.
                </p> With tail text.
                <hr/>
            </div>""")),
            [re.compile("""^<c3:?component.*?><hr></hr>
                <p>
                    Some text.
                </p> With tail text.
                </c3:?component>$""", re.LOCALE)])
        # Example where endNode is not a sibling of startNode
        # Tail text should be excluded now
        yield (LxmlRecord(etree.XML("""
            <div>
                <hr/>
                <p>
                    Some text.
                    <hr/>
                </p> With tail text.
            </div>""")),
            [re.compile("""^<c3:?component.*?><hr></hr>
                <p>
                    Some text.
                    </p></c3:?component>$""", re.LOCALE)])
        # Example where endNode is sibling of startNode ancestor
        yield (LxmlRecord(etree.XML("""
            <div>
                <p>Some text.
                    <hr/>
                </p> With tail text
                <hr/>
            </div>""")),
           [re.compile("""^<c3:?component.*?><p><hr></hr>
                </p> With tail text
                </c3:?component>$""", re.LOCALE)])


class KESpanComponentDocumentFactoryTestCase(SpanComponentDocumentFactoryTestCase):
    "ComponentDocumentFactory Test Case with SpanXPathSelectors + keepStart."
    
    def _get_config(self):
        # Return a parsed config for the object to be tested
        return etree.XML('''
        <subConfig type="documentFactory" id="componentDocumentFactory">
          <objectType>
            cheshire3.documentFactory.ComponentDocumentFactory
          </objectType>
          <source>
            <xpath ref="spanXPath" />
          </source>
          <options>
            <setting type="keepStart">0</setting>
            <setting type="keepEnd">1</setting>
            <default type="cache">0</default>
            <default type="format">component</default>
            <default type="codec">utf-8</default>
          </options>
        </subConfig>''')

    def _get_testDataAndExpected(self):
        # Simple example
        yield (LxmlRecord(etree.XML("""
            <div>
                <hr/>
                <p>
                    Some text.
                </p>
                <hr/>
            </div>""")),
            [re.compile("""^<c3:?component.*?>
                <p>
                    Some text.
                </p>
                <hr></hr></c3:?component>$""", re.LOCALE)])
        # Simple example with tail text
        yield (LxmlRecord(etree.XML("""
            <div>
                <hr/>
                <p>
                    Some text.
                </p> With tail text.
                <hr/>
            </div>""")),
            [re.compile("""^<c3:?component.*?>
                <p>
                    Some text.
                </p> With tail text.
                <hr></hr></c3:?component>$""", re.LOCALE)])
        # Example where endNode is not a sibling of startNode
        # Tail text should be excluded now
        yield (LxmlRecord(etree.XML("""
            <div>
                <hr/>
                <p>
                    Some text.
                    <hr/>
                </p> With tail text.
            </div>""")),
            [re.compile("""^<c3:?component.*?>
                <p>
                    Some text.
                    <hr></hr></p></c3:?component>$""", re.LOCALE)])
        # Example where endNode is sibling of startNode ancestor
        yield (LxmlRecord(etree.XML("""
            <div>
                <p>Some text.
                    <hr/>
                </p> With tail text
                <hr/>
            </div>""")),
           [re.compile("""^<c3:?component.*?><p>
                </p> With tail text
                <hr></hr></c3:?component>$""", re.LOCALE)])


class KBSpanComponentDocumentFactoryTestCase(SpanComponentDocumentFactoryTestCase):
    "ComponentDocumentFactory Test Case with SpanXPathSelectors + keepStart."
    
    def _get_config(self):
        # Return a parsed config for the object to be tested
        return etree.XML('''
        <subConfig type="documentFactory" id="componentDocumentFactory">
          <objectType>
            cheshire3.documentFactory.ComponentDocumentFactory
          </objectType>
          <source>
            <xpath ref="spanXPath" />
          </source>
          <options>
            <setting type="keepStart">1</setting>
            <setting type="keepEnd">1</setting>
            <default type="cache">0</default>
            <default type="format">component</default>
            <default type="codec">utf-8</default>
          </options>
        </subConfig>''')

    def _get_testDataAndExpected(self):
        # Simple example
        yield (LxmlRecord(etree.XML("""
            <div>
                <hr/>
                <p>
                    Some text.
                </p>
                <hr/>
            </div>""")),
            [re.compile("""^<c3:?component.*?><hr></hr>
                <p>
                    Some text.
                </p>
                <hr></hr></c3:?component>$""", re.LOCALE)])
        # Simple example with tail text
        yield (LxmlRecord(etree.XML("""
            <div>
                <hr/>
                <p>
                    Some text.
                </p> With tail text.
                <hr/>
            </div>""")),
            [re.compile("""^<c3:?component.*?><hr></hr>
                <p>
                    Some text.
                </p> With tail text.
                <hr></hr></c3:?component>$""", re.LOCALE)])
        # Example where endNode is not a sibling of startNode
        # Tail text should be excluded now
        yield (LxmlRecord(etree.XML("""
            <div>
                <hr/>
                <p>
                    Some text.
                    <hr/>
                </p> With tail text.
            </div>""")),
            [re.compile("""^<c3:?component.*?><hr></hr>
                <p>
                    Some text.
                    <hr></hr></p></c3:?component>$""", re.LOCALE)])
        # Example where endNode is sibling of startNode ancestor
        yield (LxmlRecord(etree.XML("""
            <div>
                <p>Some text.
                    <hr/>
                </p> With tail text
                <hr/>
            </div>""")),
           [re.compile("""^<c3:?component.*?><p><hr></hr>
                </p> With tail text
                <hr></hr></c3:?component>$""", re.LOCALE)])


class NSSpanComponentDocumentFactoryTestCase(
          SpanComponentDocumentFactoryTestCase):
    "ComponentDocumentFactory Test Case with namespaced SpanXPathSelectors."
    
    def _get_dependencyConfigs(self):
        yield etree.XML('''
        <subConfig type="selector" id="spanXPath">
            <objectType>cheshire3.selector.SpanXPathSelector</objectType>
            <source>
                <xpath xmlns:t="http.cheshire3.org/schemas/tests">t:hr</xpath>
                <xpath xmlns:t="http.cheshire3.org/schemas/tests">t:hr</xpath>
            </source>
        </subConfig>''')
        
    def _get_testDataAndExpected(self):
        # Namespaced example
        yield (LxmlRecord(etree.XML("""
            <div xmlns="http.cheshire3.org/schemas/tests">
                <hr/>
                <p>
                    Some text.
                </p>
                <hr/>
            </div>""")),
           [re.compile("""^<c3:component.*?>
                <p>
                    Some text.
                </p>
                </c3:component>$""", re.LOCALE)])
        

def load_tests(loader, tests, pattern):
    # Alias loader.loadTestsFromTestCase for sake of line lengths
    ltc = loader.loadTestsFromTestCase
    suite = ltc(ComponentDocumentFactoryTestCase)
    suite.addTests(ltc(SpanComponentDocumentFactoryTestCase))
    suite.addTests(ltc(KSSpanComponentDocumentFactoryTestCase))
    suite.addTests(ltc(KESpanComponentDocumentFactoryTestCase))
    suite.addTests(ltc(KBSpanComponentDocumentFactoryTestCase))
    suite.addTests(ltc(NSSpanComponentDocumentFactoryTestCase))
    return suite


if __name__ == '__main__':
    tr = unittest.TextTestRunner(verbosity=2)
    tr.run(load_tests(unittest.defaultTestLoader, [], 'test*.py'))
