from xml.etree.ElementTree import Element, SubElement, tostring


class AtomEntry:
    def __init__(self, title, content):
        self.title = title
        self.content = content
    

    def to_xml(self):
        entry = Element("entry", xmlns="http://www.w3.org/2005/Atom")
        title = SubElement(entry, "title")
        title.text = self.title
        content = SubElement(entry, "content", type="text/plain")
        content.text = self.content
        return tostring(entry, encoding="utf-8", method='xml').decode('utf-8')
    
# 使用例
if __name__ == "__main__":
    entry = AtomEntry("テスト記事です", "ここが本文です")
    xml_string = entry.to_xml()
    print(xml_string)