
VERSION = '0.4.4'

import zipfile, collections, os
from xml.dom import minidom

_DC_URI = "http://purl.org/dc/elements/1.1/"
_OPF_URI = "http://www.idpf.org/2007/opf"

class EpubInfoException(Exception):
	"""Represents an exception due to a malformed epub file"""
	pass

class ManifestObj(object):
	def __init__(self, epubobj, idname, href, media_type, properties=None):
		self.id = idname
		self.href = href
		self.media_type = media_type
		self.properties = properties
		self._epubobj = epubobj

	def content(self):
		fullp = os.path.normpath(os.path.join(os.path.dirname(
			self._epubobj._opfpath), self.href))
		if fullp in self._epubobj._epubf.namelist():
			return self._epubobj._epubf.read(fullp)
		return None

class SpineObj(object):
	def __init__(self, epubobj, idref, properties=None):
		self.idref = idref
		self.properties = properties
		self._epubobj = epubobj

	def content(self):
		if self.idref in self._epubobj.manifest:
			return self._epubobj.manifest[self.idref].content()
		return None

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
		titles (list): List of all book titles.
		language (list): Language codes for the book content.
		identifiers (list): Book identifiers, with value and scheme.
		description (str): Book description, can be text or HTML.
		subjects (list): String list with several subjects.
		creators (dict): Dictionary of creator names to their role and other attributes.
		contributors (dict): Dictionary of contributor names to their role and other attributes.
		cover (bytes): Cover art bytes (if present).
		manifest (list): List of manifest items (objects).
		spine (list): List of dicts that represent the book spine.
		toc (list): List dicts that contain the book TOC.
	"""
	def __init__(self, fileobj, getcover=False):
		self._fileobj = fileobj
		self._epubf = zipfile.ZipFile(fileobj, "r", allowZip64=True)
		if "META-INF/container.xml" not in self._epubf.namelist():
			raise EpubInfoException("Missing META-INF/container.xml file")
		# This XML file contains the path to the relevant metadata files
		containerfile = self._epubf.read("META-INF/container.xml")
		containerxmlf = minidom.parseString(containerfile)
		# Look for the OPF file (absolute path)
		self._opfpath = None
		for elem in containerxmlf.getElementsByTagName('rootfile'):
			if elem.hasAttribute("full-path") and elem.hasAttribute("media-type"):
				if elem.getAttribute("media-type") == "application/oebps-package+xml":
					self._opfpath = elem.getAttribute("full-path")

		if self._opfpath is None:
			raise EpubInfoException("Can't locate the OPF file in the META-INF/container.xml file")
		if self._opfpath not in self._epubf.namelist():
			raise EpubInfoException("The OPF file is missing in the ZIP file")

		# Process the OPF file for metadata
		opfxml = minidom.parseString(self._epubf.read(self._opfpath))

		# Read mandatory models
		self._metadata = self._matchonemodel(opfxml, "metadata")
		manifest = self._matchonemodel(opfxml, "manifest")
		spine    = self._matchonemodel(opfxml, "spine")

		# Read the manifest with all the resources
		self.manifest = {}
		for child in manifest.getElementsByTagNameNS("*", "item"):
			if all(child.hasAttribute(x) for x in  ["id", "href", "media-type"]):
				itemid = child.getAttribute("id")
				prop = None
				if child.hasAttribute("properties"):
					prop = child.getAttribute("properties")

				elem = ManifestObj(self, itemid,
					child.getAttribute("href"),
					child.getAttribute("media-type"), prop)
				self.manifest[itemid] = elem

		# Read the spine and its referenced TOC
		if spine.hasAttribute("toc"):
			self._spine_toc = spine.getAttribute("toc")
		else:
			self._spine_toc = None

		self.spine = []
		for child in spine.getElementsByTagNameNS("*", "itemref"):
			if child.hasAttribute("idref"):
				idref = child.getAttribute("idref")
				prop = None
				if child.hasAttribute("properties"):
					prop = child.getAttribute("properties")

				self.spine.append(SpineObj(self, idref, prop))

		# Now parse the NCX TOC
		self.toc = []
		if self._spine_toc and self._spine_toc in self.manifest:
			ncxfile = self.manifest[self._spine_toc].content()
			tocxml = minidom.parseString(ncxfile)
			for navmap in tocxml.getElementsByTagNameNS("*", "navMap"):
				self.toc += self._parseNavPoints(navmap.childNodes)

		# Proceed to process well-known fields (some are optional and return None)
		self.titles = self._getmetamulti("title")
		self.title = self.titles[0] if self.titles else None
		self.language = self._getmetamulti("language")
		self.description = self._getmetafirst("description")
		self.subjects = self._getmetamulti("subject")
		self.meta = self._getmetafull("meta")

		# Read identifiers and their schemas
		self.identifiers = []
		for ident in self._getmetafull("identifier"):
			if "" in ident:
				entry = {"value": EpubFile._wstrim(ident[""])}
				if "scheme" in ident:
					entry["scheme"] = ident["scheme"]
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
		# Clear meta fields that are used to refine authors and contributors
		wipemeta = set()
		for fld in ["creator", "contributor"]:
			for ecr in self._getmetafull(fld):
				if "id" in ecr:
					for i, elem in enumerate(self.meta):
						if "refines" in elem and "property" in elem and elem["refines"] == "#" + ecr["id"]:
							wipemeta.add(i)
		self.meta = [x for i, x in enumerate(self.meta) if i not in wipemeta]

		# Parse dates
		# <dc:date opf:event="modification/publication/creation">datehere</dc:date>
		datenodes = self._getmetafull("date")
		self.dates = {
			entry.get("event", ""): EpubFile._wstrim(entry[""])
			for entry in datenodes if "" in entry
		}

		# Parse the cover metadata to extract the image
		self.cover = None
		if getcover:
			# Look for a meta that looks like:
			# <meta name="cover" content="some_item_id"/>
			imgpath = None
			for m in self.meta:
				if m.get("name", None) == "cover":
					# Search this item in the item list
					coverid = m.get("content", None)
					if coverid in self.manifest:
						imgpath = self.manifest[coverid].href
			# Because the spec has so many possibilites we can also find by type
			if imgpath is None:
				for itemid, m in self.manifest.items():
					if m.properties == "cover-image":
						imgpath = m.href
			# Extract the href of the image, and look it up in the zip file
			if imgpath:
				imgpath = os.path.normpath(os.path.join(os.path.dirname(self._opfpath), imgpath))
				if imgpath in self._epubf.namelist():
					self.cover = self._epubf.read(imgpath)


	def _matchonemodel(self, xmldoc, mname):
		ret = xmldoc.getElementsByTagNameNS("*", mname)
		if len(ret) != 1:
			raise EpubInfoException("Exactly one `%s` is required in OPF" % mname)
		return ret[0]

	def _parsehuman(self, elem, refines):
		# Returns name and attributes. The role attribute is a set (can be empty)
		cname = EpubFile._wstrim(elem[""])
		attrs = {}
		# Load role inline, if present, otherwise look for a refine
		attrs["role"] = set([elem.get("role", None)])
		if None in attrs["role"] and "id" in elem and elem["id"] in refines:
			attrs["role"] = set(refines[elem["id"]].get("role", []))
		attrs["role"] -= set([None])
		# Same for file-as attribute
		attrs["file-as"] = elem.get("file-as", None)
		if attrs["file-as"] is None and "id" in elem and elem["id"] in refines:
			attrs["file-as"] = refines[elem["id"]].get("file-as", [None])[0]

		# Trim values as spec mandates
		attrs["file-as"] = EpubFile._wstrim(attrs["file-as"])
		attrs["role"] = set(EpubFile._wstrim(x) for x in attrs["role"])

		return (cname, attrs)

	def _getmetafirst(self, tag):
		for field in self._metadata.getElementsByTagNameNS("*", tag):
			if field.childNodes and field.childNodes[0].nodeType == field.childNodes[0].TEXT_NODE:
				return EpubFile._wstrim(field.childNodes[0].nodeValue)
		return None

	def _getmetamulti(self, tag):
		ret = []
		for field in self._metadata.getElementsByTagNameNS("*", tag):
			if field.childNodes and field.childNodes[0].nodeType == field.childNodes[0].TEXT_NODE:
				ret.append(EpubFile._wstrim(field.childNodes[0].nodeValue))
		return ret

	def _getmetafull(self, tag):
		ret = []
		for field in self._metadata.getElementsByTagNameNS("*", tag):
			entry = {}
			for attr in field.attributes.keys():
				cattr = attr.split(":")[-1]  # Strip namespace
				entry[cattr] = field.getAttribute(attr)
			if field.childNodes and field.childNodes[0].nodeType == field.childNodes[0].TEXT_NODE:
				entry[""] = field.childNodes[0].nodeValue
			ret.append(entry)
		return ret

	def _parseNavPoints(self, entities):
		ret = []
		for e in entities:
			if e.nodeType == e.ELEMENT_NODE and e.tagName == "navPoint":
				title, href = None, None
				for c in e.childNodes:
					if c.nodeType == e.ELEMENT_NODE and c.tagName == "navLabel":
						for t in c.childNodes:
							if t.nodeType == t.ELEMENT_NODE and t.tagName == "text":
								if t.firstChild:
									title = t.firstChild.nodeValue
					elif c.nodeType == e.ELEMENT_NODE and c.tagName == "content":
						if c.hasAttribute("src"):
							href = c.getAttribute("src")

				r = {
					"title": title,
					"href": href,
				}
				sube = self._parseNavPoints(e.childNodes)
				if sube:
					r["children"] = sube
				ret.append(r)
		return ret

	@staticmethod
	def _wstrim(istr):
		# According to spec, whitespace is (#x20 | #x9 | #xD | #xA)
		if istr:
			return istr.strip("\x20\x09\x0d\x0a")
		return None

	def _wipe_metafields(self, xmlelem, tag):
		for node in xmlelem.getElementsByTagNameNS("*", tag):
			node.parentNode.removeChild(node)

	def _add_metafields(self, docxml, parent, prefix, name, value, attrs={}):
		if prefix:
			node = docxml.createElement(prefix + ":" + name)
		else:
			node = docxml.createElement(name)
		if value is not None:
			node.appendChild(docxml.createTextNode(value))
		for aname, value in attrs.items():
			node.setAttribute(aname, value)
		parent.appendChild(node)

	def _get_namespaces(self, xmlelem):
		ret = {}
		for name, val in xmlelem.attributes.items():
			if name.startswith("xmlns:"):
				ret[val] = name.split(":")[1]
		return ret

	# Generate a metadata OPF file with the updated metadata fields
	def serialize_metadata(self):
		# Read original XML to update
		opfxml = minidom.parseString(self._epubf.read(self._opfpath))
		metadata = self._matchonemodel(opfxml, "metadata")

		# Ensure we have the relevant namespace prefixes
		ns = self._get_namespaces(metadata)
		if _DC_URI not in ns:
			metadata.setAttribute("xmlns:dc", _DC_URI)
		if _OPF_URI not in ns:
			metadata.setAttribute("xmlns:opf", _OPF_URI)
		ns = self._get_namespaces(metadata)
		dcns, opfns = ns[_DC_URI], ns[_OPF_URI]

		# Remove the relevant fields
		for f in ["title", "subject", "language", "description", "creator", "contributor", "meta", "date"]:
			self._wipe_metafields(metadata, f)

		for t in self.titles:
			self._add_metafields(opfxml, metadata, dcns, "title", t)
		for s in self.subjects:
			self._add_metafields(opfxml, metadata, dcns, "subject", s)
		for l in self.language:
			self._add_metafields(opfxml, metadata, dcns, "language", l)
		for evname, val in self.dates.items():
			if evname:
				self._add_metafields(opfxml, metadata, dcns, "date", val, {opfns + ":event": evname})
			else:
				self._add_metafields(opfxml, metadata, dcns, "date", val)
		if self.description is not None:
			self._add_metafields(opfxml, metadata, dcns, "description", self.description)
		for tag, emap in [("creator", self.creators), ("contributor", self.contributors)]:
			for value, attrs in emap.items():
				if "file-as" in attrs:
					nodeatr = {opfns + ":file-as": attrs["file-as"]}
				else:
					nodeatr = {}

				if "role" in attrs:
					for r in attrs["role"]:
						nodeatr[opfns + ":role"] = r
						self._add_metafields(opfxml, metadata, dcns, tag, value, nodeatr)
				else:
					self._add_metafields(opfxml, metadata, dcns, tag, value, nodeatr)
		for m in self.meta:
			ma = {k: v for k, v in m.items() if k}
			val = m[""] if "" in m else None
			self._add_metafields(opfxml, metadata, None, "meta", val, ma)

		# Beautify the XML a bit
		l = []
		for node in metadata.childNodes:
			if node.nodeType != node.TEXT_NODE:
				l.append(node)
		for node in list(metadata.childNodes):
			metadata.removeChild(node)
		assert len(metadata.childNodes) == 0
		for node in l:
			metadata.appendChild(node)
			metadata.appendChild(opfxml.createTextNode("\n"))
		return opfxml.toxml()

	# Produce a new epub file with an updated (serialized) OPF file
	def write_epub(self, fileobj):
		with zipfile.ZipFile(self._fileobj, "r") as izip:
			with zipfile.ZipFile(fileobj, "w", allowZip64=True) as ozip:
				# Write mimetype (uncompressed!)
				ozip.writestr("mimetype", b"application/epub+zip", compress_type=zipfile.ZIP_STORED)

				# Proceed to write the OPF
				ozip.writestr(self._opfpath, self.serialize_metadata())

				# Now just copy all the other files
				for finfo in izip.infolist():
					if finfo.filename not in ozip.namelist():
						ozip.writestr(finfo, izip.read(finfo.filename), compress_type=zipfile.ZIP_DEFLATED)


