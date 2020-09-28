epubinfo
========

A python3 epub library for metadata extraction

The aim of this library is to easily extract any useful metadata from an epub
file including accessories to get cover art.

How to use it
-------------

```python
import epubinfo
metadata = epubinfo.EpubFile(open("somefile.epub", "rb"), getcover=True)
print(metadata.title)
open("cover.jpg", "wb").write(metadata.cover)
```


