from twisted.web.template import Element, XMLString, flattenString, renderer, tags, Namespace
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


class UseNamespaces(Element):
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
            yield ClientNamespace(tag.clone().fillSlots(clientName=client['clientName']), client)


class ClientNamespace(Namespace):
    def __init__(self, tag, client):
        Namespace.__init__(self, tag)
        self.client = client

    @renderer
    def contacts(self, request, tag):
        for contact in self.client['contacts']:
            yield tag.clone().fillSlots(contactName=contact)


flattenString(None, UseNamespaces()).addCallback(println)
