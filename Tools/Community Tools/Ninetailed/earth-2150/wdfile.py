from io import BytesIO, SEEK_CUR, SEEK_END
import os.path
import zlib


class Resource:
	def __init__(self):
		self.name = ''
		self.filetype = 0
		self.offset = 0
		self.length = 0
		self.decompressed = 0
		self.supplementary_data = None

	def __repr__(self):
		return f'Resource(name=\'{self.name}\', type={self.filetype}, offset={self.offset}, length={self.length}, decompressed={self.decompressed}, supplementary_data={self.supplementary_data})'


def readint(stream, bytecount=4):
	return int.from_bytes(stream.read(bytecount), byteorder='little')

def readname(stream):
	namelen = stream.read(1)
	if len(namelen) == 0: return None
	namedata = stream.read(namelen[0])
	try:
		return namedata.decode(encoding='latin_1')
	except:
		print(namedata)
		raise

def readsupplementary(filetype, stream):
	if filetype == 9:
		return readname(stream)
	elif filetype == 17:
		return stream.read(4)
	elif filetype == 30:
		return readname(stream)
	elif filetype == 33:
		return stream.read(16)
	elif filetype == 43:
		return (readname(stream), stream.read(16))
	elif filetype == 49:
		return stream.read(20)
	elif filetype == 57:
		return (readname(stream), stream.read(20))
	elif filetype == 59:
		return (readname(stream), stream.read(20))
	else:
		return None

def readindex(filename):
	with open(filename, 'rb') as wdfile:
		wdfile.seek(-4, SEEK_END)
		dirlen = readint(wdfile)
		wdfile.seek(-dirlen, SEEK_END)
		dirraw = zlib.decompress(wdfile.read())
		dirdata = BytesIO(dirraw)

	files = []

	dirdata.seek(10)
	while True:
		name = readname(dirdata)
		if name is None: break
		res = Resource()
		res.name = name
		res.filetype = dirdata.read(1)[0]
		if res.filetype == 255:
			res.supplementary_data = dirdata.read(3)
		else:
			res.offset = readint(dirdata)
			res.length = readint(dirdata)
			res.decompressed = readint(dirdata)
			res.supplementary_data = readsupplementary(res.filetype, dirdata)
		files.append(res)

	return files

os.chdir('C:/Games/Earth 2150 - The Moon Project/WDFiles')
for filename in os.scandir():
	if not filename.is_file() or not filename.name[-3:] == '.wd': continue
	resources = readindex(filename)
	print(filename)
	with open(filename, 'rb') as wdfile:
		for res in resources:
			if res.filetype == 255: continue
			print(res.name)
			respath = res.name.split('\\')
			dirname = '/'.join(respath[:-1])
			if dirname:
				os.makedirs(dirname, exist_ok=True)

			with open('/'.join(respath), 'wb') as outfile:
				wdfile.seek(res.offset)
				if res.length == res.decompressed:
					outfile.write(wdfile.read(res.length))
				else:
					decompress = zlib.decompressobj()
					outfile.write(decompress.decompress(wdfile.read(res.length)))
					while not decompress.eof:
						outfile.write(decompress.decompress())
