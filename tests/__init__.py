
import os, unittest, io, zipfile, hashlib
import epubinfo
import tests.data as testdata

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

	def test_parse_manifest(self):
		for testf, refdata in testdata.TEST_CONTENT.items():
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
				# Check manifest and spine
				self.assertEqual(res.toc, refdata["toc"])
				self.assertEqual(len(refdata["items"]), len(res.manifest))
				self.assertEqual(len(refdata["spine"]), len(res.spine))

				for it in refdata["items"]:
					self.assertIn(it["id"], res.manifest)
					self.assertEqual(it["href"], res.manifest[it["id"]].href)
					self.assertEqual(it["media-type"], res.manifest[it["id"]].media_type)
					self.assertEqual(it["properties"], res.manifest[it["id"]].properties)
					self.assertEqual(it["content"], hashlib.sha256(res.manifest[it["id"]].content()).hexdigest())

				for i, it in enumerate(refdata["spine"]):
					self.assertEqual(it["idref"], res.spine[i].idref)
					self.assertEqual(it["content"], hashlib.sha256(res.spine[i].content()).hexdigest())

	def test_parse_metadata(self):
		for testf, refdata in testdata.TEST_METADATA.items():
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
				self.assertEqual(res.titles, refdata["titles"])
				self.assertEqual(res.description, refdata["description"])
				self.assertEqual(res.identifiers, refdata["identifiers"])
				self.assertEqual(res.language, refdata["language"])
				self.assertEqual(res.subjects, refdata["subjects"])
				self.assertEqual(res.dates, refdata["date"])
				self.assertEqual(res.creators, refdata["creators"])
				self.assertEqual(res.contributors, refdata["contributors"])
				if refdata["cover"] is None:
					self.assertEqual(res.cover, None)
				else:
					self.assertEqual(hashlib.sha256(res.cover).hexdigest(), refdata["cover"])

