from twisted.web.template import Element, XMLString, flattenString, renderer, tags
from twisted.python.util import println


clientData = [
    {'clientName': 'Acme',
    'contacts': [
        'bob@acme.com',
        'alice@acme.com'
    ]},

    {'clientName': 'Yoyodyne',
    'contacts': [
        'bob@yoyodyne.com',
        'alice@yoyodyne.com'
    ]},
]


class OneRenderer(Element):
    loader = XMLString('''
        <html xmlns:t="http://twistedmatrix.com/ns/twisted.web.template/0.1">
            <ul>
                <li t:render='clients'>
                    <t:slot name='clientName' />
                    <ul>
                        <t:slot name='contacts' />
                    </ul>
                </li>
            </ul>
        </html>
    ''')

    @renderer
    def clients(self, request, tag):
        for client in clientData:
            clientTag = tag.clone().fillSlots(clientName=client['clientName'])
            for contact in client['contacts']:
                # how do I know what part of the template to clone for each
                # contact? In Nevow, I could use a pattern.
                pass

            # alternate solution:

            clientTag.fillSlots(contacts=map(tags.li, client['contacts']))

            # However, I have taken a decision about data presentation (each
            # contact should be in a <li> element) away from the template and
            # put it in my code. I could put it in a seprate file, but is that
            # really much better?

            # What if I am a web designer or a maintainer and I want to modify
            # how contacts are rendered? I read the template, and I'm presented
            # only with an opaque <t:slot>. How do I know where to look next?
            # Yes, the render method should have documentation, and could
            # document that there's another template in another file. But isn't
            # that too complicated for such a simple task?

            yield clientTag


class TwoRenderers(Element):
    loader = XMLString('''
        <html xmlns:t="http://twistedmatrix.com/ns/twisted.web.template/0.1">
            <ul>
                <li t:render='clients'>
                    <t:slot name='clientName' />
                    <ul>
                        <li t:render='contacts'>
                            <t:slot name='contactName' />
                        </li>
                    </ul>
                </li>
            </ul>
        </html>
    ''')

    @renderer
    def clients(self, request, tag):
        for client in clientData:
            yield tag.clone().fillSlots(clientName=client['clientName'])

    @renderer
    def contacts(self, request, tag):
        # in nevow I could receive information about which client through the
        # data parameter.
        tag.fillSlots(contactName='how do I know which client?')
        return tag


flattenString(None, OneRenderer()).addCallback(println)
flattenString(None, TwoRenderers()).addCallback(println)
