from twisted.web import microdom as dom

# This should render to:
#
# <event xmlns="http://example.com/ns/stream/event"
#        xmlns:entity="http://example.com/ns/stream/entity">
#   <entity:entity event-attr="on_entity">
#     <entity:name><![CDATA[John Wayne]]></entity:name>
#   </entity:entity>
# </event>
#
# Of course, I could have put name in an attribute, but that's not the point
# 
# Instead, renders as follows
#
# <event xmlns="http://example.com/ns/stream/event"
#        xmlns:entity="http://example.com/ns/stream/entity">
#   <entity:entity event-attr="on_entity">
#     <name><![CDATA[John Wayne]]></name>
#   </entity>
# </event>

doc = dom.Document()
root = doc.createElement("event", 
    namespace = "http://example.com/ns/stream/event")

entity = doc.createElement("entity",
    namespace = "http://example.com/ns/stream/entity")

# repeating the namespace is not so fun, but is probably better if the
# developer then starts to move stuff around
url = doc.createElement("name",
    namespace = "http://example.com/ns/stream/entity")
url.appendChild(dom.CDATASection("John Wayne"))
entity.appendChild(url)

entity.setAttribute("event-attr", "on_entity")
root.appendChild(entity)
root.addPrefixes({entity.namespace: 'entity'})

doc.appendChild(root)

print root.toxml()
