
import os, unittest, io, zipfile, hashlib
import epubinfo
import tests.data as testdata

class EpubTestFiles(unittest.TestCase):

	@staticmethod
	def _gen_epub(fileobj, filep):
		# Builds an epub based on the testing files in the specified directory
		with zipfile.ZipFile(fileobj, "w", compression=zipfile.ZIP_STORED) as zf:
			for bpath, _, sfiles in os.walk(filep):
				for fn in sfiles:
					zippath = os.path.join(bpath[len(filep) + 1:], fn)
					with open(os.path.join(bpath, fn), "rb") as tmpfd:
						zf.writestr(zippath, tmpfd.read())

	def test_parse_empty(self):
		with io.BytesIO() as fakefile:
			with zipfile.ZipFile(fakefile, "w") as zf:
				zf.writestr("foo.txt", "bar")
			with self.assertRaisesRegex(epubinfo.EpubInfoException, "Missing.*container.xml"):
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
			with self.assertRaisesRegex(epubinfo.EpubInfoException, "The OPF file is missing"):
				epubinfo.EpubFile(fakefile)

	def test_parse_missing_opf_entry(self):
		with io.BytesIO() as fakefile:
			with zipfile.ZipFile(fakefile, "w") as zf:
				zf.writestr("META-INF/container.xml", '<?xml version="1.0"?><foo></foo>')
			with self.assertRaisesRegex(epubinfo.EpubInfoException, "Can't locate the OPF file.*"):
				epubinfo.EpubFile(fakefile)

	def test_parse_duplicated_metadata(self):
		for tname, metafield in [('broken1', 'metadata'), ('broken2', 'manifest'), ('broken3', 'spine')]:
			basepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', tname)
			# Construct a FileObj that contains a ZIP with the right data
			with io.BytesIO() as fakefile:
				self._gen_epub(fakefile, basepath)
				with self.assertRaisesRegex(epubinfo.EpubInfoException, "Exactly one `%s`" % metafield):
					epubinfo.EpubFile(fakefile, getcover=True)

	def test_parse_manifest(self):
		for testf, refdata in testdata.TEST_CONTENT.items():
			basepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', testf)
			# Construct a FileObj that contains a ZIP with the right data
			with io.BytesIO() as fakefile:
				self._gen_epub(fakefile, basepath)
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
				self._gen_epub(fakefile, basepath)
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
				self.assertEqual(res.meta, refdata["meta"])

	def test_patch_metadata(self):
		for testf in testdata.PATCH_TESTS:
			basepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', testf)
			# Construct a FileObj that contains a ZIP with the right data
			with io.BytesIO() as fakefile:
				self._gen_epub(fakefile, basepath)
				# Go ahead and test
				meta1 = epubinfo.EpubFile(fakefile, getcover=True)
				# Re-pack in a new epub and compare
				with io.BytesIO() as fakefile2:
					meta1.write_epub(fakefile2)
					meta2 = epubinfo.EpubFile(fakefile2, getcover=True)

					# Check results
					self.assertEqual(meta1.titles, meta2.titles)
					self.assertEqual(meta1.language, meta2.language)
					self.assertEqual(meta1.subjects, meta2.subjects)
					self.assertEqual(meta1.description, meta2.description)
					self.assertEqual(meta1.creators, meta2.creators)
					self.assertEqual(meta1.contributors, meta2.contributors)
					self.assertEqual(meta1.meta, meta2.meta)

				# Attempt to change some fields and do it again
				meta1.titles = ["Title 1", "Second title"]
				meta1.description = "Example desc"
				meta1.subjects = ["Foo", "Bar"]
				meta1.language = ["en", "fr"]
				meta1.creators = {
					"Name Surname": {"file-as": "Surname, Name"},
					"Someauth Foo": {"file-as": "Someauth Foo", "role": set({"aut", "trn"})}}
				meta1.contributors = {
					"Hey There": {"file-as": "Testing"},
					"More stuff": {"role": set({"aut", "trn"})}}
				meta1.dates = { "": "2010", "modification": "2020-12-12" }
				with io.BytesIO() as fakefile3:
					meta1.write_epub(fakefile3)
					meta3 = epubinfo.EpubFile(fakefile3, getcover=True)

					# Check results
					self.assertEqual(meta1.titles, meta3.titles)
					self.assertEqual(meta1.language, meta3.language)
					self.assertEqual(meta1.subjects, meta3.subjects)
					self.assertEqual(meta1.dates, meta3.dates)
					self.assertEqual(meta1.description, meta3.description)
					self.assertEqual(meta1.creators, meta3.creators)
					self.assertEqual(meta1.contributors, meta3.contributors)
					self.assertEqual(meta1.meta, meta3.meta)

