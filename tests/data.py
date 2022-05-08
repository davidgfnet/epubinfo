

# Reference data for response checking
TEST_METADATA = {
	"accessible_epub_3": {
		"title": "Accessible EPUB 3",
		"titles": ["Accessible EPUB 3"],
		"description": None,
		"identifiers": [
			{"value": "urn:isbn:9781449328030"},
		],
		"language": ["en"],
		"subjects": [],
		"date": {"": "2012-02-20"},
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
	"epub3-spec": {
		"title": "EPUB 3.0 Specification",
		"titles": ["EPUB 3.0 Specification"],
		"description": None,
		"identifiers": [
			{"value": "code.google.com.epub-samples.epub30-spec"},
		],
		"language": ["en"],
		"subjects": [],
		"date": {},
		"creators": {
			"EPUB 3 Working Group": {},
		},
		"contributors": {},
		"cover": "d738460b51aef898e5a2a4d8261a57a9c67f3a6f5816e6813c9258323399de65",
	},
	"cc-shared-culture": {
		"title": "Creative Commons - A Shared Culture",
		"titles": ["Creative Commons - A Shared Culture"],
		"description": "Multiple video tests (see Navigation Document (toc) for details)",
		"identifiers": [
			{"value": "code.google.com.epub-samples.cc-shared-culture"},
		],
		"language": ["en-US"],
		"subjects": [],
		"date": {},
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
		"titles": ["Moby-Dick"],
		"description": None,
		"identifiers": [
			{"value": "code.google.com.epub-samples.moby-dick-basic"},
		],
		"language": ["en-US"],
		"subjects": ["Novel", "Adventures"],
		"date": {},
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
		"titles": ["This is an example title"],
		"description": None,
		"identifiers": [
			{"value": "someid"},
			{"scheme": "isbn", "value": "9780000000001"},
			{"scheme": "doi", "value": "doi:10.1016/j.iheduc.2008.03.001"},
			{"scheme": "uuid", "value": "50f9f8b1-8a81-4dd5-b104-0766188d7d2c"},
		],
		"language": ["en-US", "en-UK"],
		"subjects": [],
		"date": {"": "2012-02-20", "modification": "2018-11-19"},
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
		"titles": [
			"World Cultures and Geography",
			"Legends of Landforms",
			"Why Snails Have Shells",
		],
		"description": None,
		"identifiers": [
			{"value": "41f1328c-0571-4e71-8be8-e65bc148281a"},
		],
		"language": ["en-US"],
		"subjects": [],
		"date": {},
		"creators": {},
		"contributors": {},
		"cover": None,
	},
	"covertest": {
		"title": "Some title",
		"titles": ["Some title"],
		"description": "Lorem ipsum.",
		"identifiers": [],
		"language": [],
		"subjects": [],
		"date": {},
		"creators": {'Foo Bar': {'file-as': 'Foo Bar', 'role': {'aut'}}},
		"contributors": {},
		"cover": "f2f18ddff9003fd06590c6e94a8a6848b48c6566560d6dddd86dd9445b9b81d5",
	},
}

# Reference data for response checking
TEST_CONTENT = {
	"covertest": {
		"items": [
			{ "id": "text.html", "media-type": "application/xhtml+xml",
			  "href": "Text/text.html", "properties": None,
			  "content": "b1aa97fe1f64bec7de135cabb2b914341ff61765a6dd20b83d05ba7e24245229" },
			{ "id": "text-2.html", "media-type": "application/xhtml+xml",
			  "href": "Text/text2.html", "properties": None,
			  "content": "b1aa97fe1f64bec7de135cabb2b914341ff61765a6dd20b83d05ba7e24245229" },
			{ "id": "text-3.html", "media-type": "application/xhtml+xml",
			  "href": "Text/text3.html", "properties": None,
			  "content": "b1aa97fe1f64bec7de135cabb2b914341ff61765a6dd20b83d05ba7e24245229" },
			{ "id": "cover.jpg", "media-type": "image/jpeg",
			  "href": "images/cover.jpg", "properties": None,
			  "content": "f2f18ddff9003fd06590c6e94a8a6848b48c6566560d6dddd86dd9445b9b81d5"},
			{ "id": "ncx", "media-type": "application/x-dtbncx+xml",
			  "href": "toc.ncx", "properties": None,
			  "content": "5bb5fe774fa1569fa6738959b4fda3c89bf622995dc3a723ed2daa3b866b03ed"},
		],
		"spine": [
			{"idref": "text.html",
			  "content": "b1aa97fe1f64bec7de135cabb2b914341ff61765a6dd20b83d05ba7e24245229" },
			{"idref": "text-2.html",
			  "content": "b1aa97fe1f64bec7de135cabb2b914341ff61765a6dd20b83d05ba7e24245229" },
			{"idref": "text-3.html",
			  "content": "b1aa97fe1f64bec7de135cabb2b914341ff61765a6dd20b83d05ba7e24245229" },
		],
		"toc": [
			{'title': 'Chapter 1',
			 'href': 'Text/text.xhtml',
			 'children': [
				{'title': '2',
				 'href': 'Text/text1.xhtml'},
				{'title': '3',
				 'href': 'Text/text2.xhtml'},
				{'title': None,
				 'href': 'Text/text2.xhtml#endofbook'},
			 ]
			}
		],
	}
}

PATCH_TESTS = [
	'accessible_epub_3',
	'epub3-spec',
	'cc-shared-culture',
	'moby-dick',
	'torture',
	'WCAG',
	'covertest'
]


