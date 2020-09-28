
VERSION = '0.1.0'

import zipfile, collections, os, re
from xml.dom import minidom

class EpubInfoException(Exception):
	"""Represents an exception due to a malformed epub file"""
	pass

class EpubFile(object):
	"""
	Extracts metadata info from a file object.

    Processes the file object to extract metadata from it. It can optionally
    extract the book cover as well. Can throw exceptions if the book is
    completely malformed, however lack of metadata or cover art won't throw
    any exceptions.

    Args:
        fileobj (obj): File Object of the file that will be processed.
        getcover (boolean): Whether to extract the cover art from the book.

    Attributes:
        title (str): Book title.
        language (str): Language code for the book content.
        identifiers (list): Book identifiers, with value and scheme.
        description (str): Book description, can be text or HTML.
        subjects (list): String list with several subjects.
        creators (dict): Dictionary of creator names to their role and other attributes.
        contributors (dict): Dictionary of contributor names to their role and other attributes.
        cover (bytes): Cover art bytes (if present).

    """
	def __init__(self, fileobj, getcover=False):
		epubf = zipfile.ZipFile(fileobj, "r", allowZip64=True)
		if "META-INF/container.xml" not in epubf.namelist():
			raise EpubInfoException("Missing META-INF/container.xml file")
		# This XML file contains the path to the relevant metadata files
		containerfile = epubf.read("META-INF/container.xml")
		containerxmlf = minidom.parseString(containerfile)
		# Look for the OPF file (absolute path)
		opffile = None
		for elem in containerxmlf.getElementsByTagName('rootfile'):
			if elem.hasAttribute("full-path") and elem.hasAttribute("media-type"):
				if elem.getAttribute("media-type") == "application/oebps-package+xml":
					opffile = elem.getAttribute("full-path")

		if opffile is None:
			raise EpubInfoException("Can't locate the OPF file in the META-INF/container.xml file")
		if opffile not in epubf.namelist():
			raise EpubInfoException("The OPF file is missing in the ZIP file")

		# Process the OPF file for metadata
		opfxml = minidom.parseString(epubf.read(opffile))
		# Get all metadata sections and their metadata children
		self._metafields = []
		for elem in opfxml.getElementsByTagNameNS("*", "metadata"):
			for child in elem.childNodes:
				if child.nodeType == child.ELEMENT_NODE:
					self._metafields.append(child)

		# Proceed to process well-known fields (some are optional and return None)
		self.title = self._getmeta("title")
		self.language = self._getmeta("language")
		self.description = self._getmeta("description")
		self.subjects = self._getmetamulti("subject")
		self.meta = self._getmetafull("meta")

		# Read identifiers and their schemas
		self.identifiers = []
		for ident in self._getmetafull("identifier"):
			if "" in ident:
				entry = {"value": ident[""]}
				if "opf:scheme" in ident:
					entry["scheme"] = ident["opf:scheme"]
				self.identifiers.append(entry)
		
		# Load refines, some formats (epub3.2 but also older ones) use this instead of inline attrs
		# <meta refines="#creator12" property="file-as">Smith, John</meta>
		refines = collections.defaultdict(lambda: collections.defaultdict(list))
		for elem in self.meta:
			if "refines" in elem and "property" in elem and elem["refines"].startswith("#"):
				refines[elem["refines"][1:]][elem["property"]].append(elem[""])

		# Parse the creators and contributors
		self.creators, self.contributors = {}, {}
		for elem in self._getmetafull("creator"):
			if "" in elem:   # Skip authors without a valid name
				cname, attrs = self._parsehuman(elem, refines)
				if cname in self.creators:
					self.creators[cname]["role"] |= attrs["role"]
				else:
					self.creators[cname] = attrs
		for elem in self._getmetafull("contributor"):
			if "" in elem:
				cname, attrs = self._parsehuman(elem, refines)
				if cname in self.contributors:
					self.contributors[cname]["role"] |= attrs["role"]
				else:
					self.contributors[cname] = attrs
		# Clean up empty fields
		for cname in self.creators.keys():
			self.creators[cname] = {k: v for k, v in self.creators[cname].items() if v}
		for cname in self.contributors.keys():
			self.contributors[cname] = {k: v for k, v in self.contributors[cname].items() if v}

		# Parse dates
		# <dc:date opf:event="modification/publication/creation">datehere</dc:date>
		datenodes = self._getmetafull("date")
		self.dates = { entry.get("opf:event", ""): entry[""] for entry in datenodes if "" in entry }

		# Parse the cover metadata to extract the image
		self.cover = None
		if getcover:
			# Extract all the items in the manifest first
			items = []
			for elem in opfxml.getElementsByTagNameNS('*', 'manifest'):
				for child in elem.childNodes:
					if child.nodeType == child.ELEMENT_NODE:
						if re.match("(.*:)?item", child.tagName):
							items.append(child)

			# Look for a meta that looks like:
			# <meta name="cover" content="some_item_id"/>
			coveritem = None
			for m in self.meta:
				if m.get("name", None) == "cover":
					# Search this item in the item list
					coverid = m.get("content", None)
					for it in items:
						if it.hasAttribute("id") and it.getAttribute("id") == coverid:
							coveritem = it
			# Because the spec has so many possibilites we can also find by type
			if coveritem is None:
				for it in items:
					if it.hasAttribute("properties") and it.getAttribute("properties") == "cover-image":
						coveritem = it
			# Extract the href of the image, and look it up in the zip file
			if coveritem and coveritem.hasAttribute("href"):
				imgpath = coveritem.getAttribute("href")
				imgpath = os.path.normpath(os.path.join(os.path.dirname(opffile), imgpath))
				if imgpath in epubf.namelist():
					self.cover = epubf.read(imgpath)

		epubf.close()


	def _parsehuman(self, elem, refines):
		# Returns name and attributes. The role attribute is a set (can be empty)
		cname = elem[""]
		attrs = {}
		# Load role inline, if present, otherwise look for a refine
		attrs["role"] = set([elem.get("opf:role", None)])
		if None in attrs["role"] and "id" in elem and elem["id"] in refines:
			attrs["role"] = set(refines[elem["id"]].get("role", []))
		attrs["role"] -= set([None])
		# Same for file-as attribute
		attrs["file-as"] = elem.get("opf:file-as", None)
		if attrs["file-as"] is None and "id" in elem and elem["id"] in refines:
			attrs["file-as"] = refines[elem["id"]].get("file-as", [None])[0]

		return (cname, attrs)

	def _getmeta(self, tag):
		for field in self._metafields:
			if re.match("(.*:)?" + tag, field.tagName):
				if field.childNodes and field.childNodes[0].nodeType == field.childNodes[0].TEXT_NODE:
					return field.childNodes[0].nodeValue
		return None

	def _getmetamulti(self, tag):
		ret = []
		for field in self._metafields:
			if re.match("(.*:)?" + tag, field.tagName):
				if field.childNodes and field.childNodes[0].nodeType == field.childNodes[0].TEXT_NODE:
					ret.append(field.childNodes[0].nodeValue)
		# Sort for consistency
		return sorted(ret)

	def _getmetafull(self, tag):
		ret = []
		for field in self._metafields:
			if re.match("(.*:)?" + tag, field.tagName):
				entry = {}
				for attr in field.attributes.keys():
					entry[attr] = field.getAttribute(attr)
				if field.childNodes and field.childNodes[0].nodeType == field.childNodes[0].TEXT_NODE:
					entry[""] = field.childNodes[0].nodeValue
				ret.append(entry)
		return ret


