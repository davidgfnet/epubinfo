
import os, unittest, io, zipfile, hashlib
import epubinfo

class EpubTestFiles(unittest.TestCase):

	def test_parse_empty(self):
		with io.BytesIO() as fakefile:
			with zipfile.ZipFile(fakefile, "w") as zf:
				zf.writestr("foo.txt", "bar")
			with self.assertRaises(epubinfo.EpubInfoException):
				epubinfo.EpubFile(fakefile)

	def test_parse_missing_opf(self):
		with io.BytesIO() as fakefile:
			with zipfile.ZipFile(fakefile, "w") as zf:
				zf.writestr("META-INF/container.xml",
					"""<?xml version="1.0" encoding="UTF-8"?>
					<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
						<rootfiles>
							<rootfile full-path="OPS/package.opf" media-type="application/oebps-package+xml"/>
						</rootfiles>
					</container>""")
			with self.assertRaises(epubinfo.EpubInfoException):
				epubinfo.EpubFile(fakefile)

	def test_parse_missing_opf_entry(self):
		with io.BytesIO() as fakefile:
			with zipfile.ZipFile(fakefile, "w") as zf:
				zf.writestr("META-INF/container.xml", '<?xml version="1.0"?><foo></foo>')
			with self.assertRaises(epubinfo.EpubInfoException):
				epubinfo.EpubFile(fakefile)

	def test_parse_metadata(self):
		for testf, refdata in EpubTestFiles.TEST_DATA.items():
			basepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', testf)
			# Construct a FileObj that contains a ZIP with the right data
			with io.BytesIO() as fakefile:
				with zipfile.ZipFile(fakefile, "w") as zf:
					for bpath, _, sfiles in os.walk(basepath):
						for fn in sfiles:
							zippath = os.path.join(bpath[len(basepath) + 1:], fn)
							with open(os.path.join(bpath, fn), "rb") as tmpfd:
								zf.writestr(zippath, tmpfd.read())
				# Go ahead and test
				res = epubinfo.EpubFile(fakefile, getcover=True)
				# Check results
				self.assertEqual(res.title, refdata["title"])
				self.assertEqual(res.description, refdata["description"])
				self.assertEqual(res.identifier, refdata["identifier"])
				self.assertEqual(res.language, refdata["language"])
				self.assertEqual(res.subjects, refdata["subjects"])
				self.assertEqual(res.creators, refdata["creators"])
				self.assertEqual(res.contributors, refdata["contributors"])
				if refdata["cover"] is None:
					self.assertEqual(res.cover, None)
				else:
					self.assertEqual(hashlib.sha256(res.cover).hexdigest(), refdata["cover"])

	# Reference data for response checking
	TEST_DATA = {
		"accessible_epub_3": {
			"title": "Accessible EPUB 3",
			"description": None,
			"identifier": "urn:isbn:9781449328030",
			"language": "en",
			"subjects": [],
			"creators": {
				"Matt Garrish": {},
			},
			"contributors": {
				"O’Reilly Production Services": {},
				"David Futato": {},
				"Robert Romano": {},
				"Brian Sawyer": {},
				"Dan Fauxsmith": {},
				"Karen Montgomery": {},
			},
			"cover": "d86dc63631ad83ca6bd27dde379771b0ebd08c291b0de1ef368d1da952580af0",
		},
		"cc-shared-culture": {
			"title": "Creative Commons - A Shared Culture",
			"description": "Multiple video tests (see Navigation Document (toc) for details)",
			"identifier": "code.google.com.epub-samples.cc-shared-culture",
			"language": "en-US",
			"subjects": [],
			"creators": {
				"Jesse Dylan": {},
			},
			"contributors": {
				"mgylling": {},
			},
			"cover": "a882a31d4bb09bdac2820f4934775b977a3cb13f3101fbc3ada85b6aec16f8c2",
		},
		"moby-dick": {
			"title": "Moby-Dick",
			"description": None,
			"identifier": "code.google.com.epub-samples.moby-dick-basic",
			"language": "en-US",
			"subjects": ["Adventures", "Novel"],
			"creators": {
				"Herman Melville": {"role": set(["aut"]), "file-as": "MELVILLE, HERMAN"},
			},
			"contributors": {
				"Dave Cramer": {"role": set(["mrk"])},
			},
			"cover": "f2f18ddff9003fd06590c6e94a8a6848b48c6566560d6dddd86dd9445b9b81d5",
		},
		"torture": {
			"title": "This is an example title",
			"description": None,
			"identifier": "someid",
			"language": "en",
			"subjects": [],
			"creators": {
				"Matt Garrish": {"role": set(["aut", "edt"])},
			},
			"contributors": {
				"O’Reilly Production Services": {"role": set(["bkp"])},
				"David Futato": {"role": set(["trl"])},
				"Robert Romano": {"role": set(["ill", "adi"])},
				"Brian Sawyer": {"role": set(["crr"])},
				"Dan Fauxsmith": {"role": set(["cmp", "arr"])},
				"Karen Montgomery": {"role": set(["cmp"]), "file-as": "Montgomery, Karen"},
			},
			"cover": "d86dc63631ad83ca6bd27dde379771b0ebd08c291b0de1ef368d1da952580af0",
		},
		"WCAG": {
			"title": "World Cultures and Geography",
			"description": None,
			"identifier": "41f1328c-0571-4e71-8be8-e65bc148281a",
			"language": "en-US",
			"subjects": [],
			"creators": {},
			"contributors": {},
			"cover": None,																																																																								
		},
	}

