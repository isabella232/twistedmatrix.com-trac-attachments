import os, os.path
import re

def check_file(filename):
	file = open(filename, 'r')
	text = file.read()
	file.close()
	
	i = text.find('__all__')

	if i>0:
		module_name = re.sub('(\.py)|(\.\/)', '', filename) 
		module_name = re.sub('\/', '.', module_name) 
		module_name = re.sub('\.__init__', '', module_name) 
		
		#check via importing
		print "[importing]", module_name,
		try:
			exec "from %s import *" % module_name
			print "[OK]", module_name
		except AttributeError:
			print "[Attribute Error]"
		except ImportError as e:
			print "[Import error]\n\t'%s'"	% e.message
		except Exception as e:
			print "[Error]\n\t%s:%s" %(type(e), e.message)
		
		#check attributes
		try:
			exec "import %s as mod" % module_name
			if hasattr(mod, '__all__'):
				for a in mod.__all__:
					if not hasattr(mod, a):
						print "\tmodule %s doesnt have attribute %s" %  \
							(module_name, a)
		except Exception as e:
			print type(e)			
	
def get_files(start_dir):
	

	directories = [start_dir]
	files=[]
	while len(directories)>0:
	    directory = directories.pop()
	    for name in os.listdir(directory):
		fullpath = os.path.join(directory,name)
		if os.path.isfile(fullpath) and re.match('.*?\.py$', fullpath):
			files.append(fullpath)
		elif os.path.isdir(fullpath):
			directories.append(fullpath)  # It's a directory, store it.
	return files

if __name__ == '__main__':
	files = get_files('.')
	for f in files:
		check_file(f)
	    
	    

