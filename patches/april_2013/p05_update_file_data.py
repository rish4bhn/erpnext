import webnotes, webnotes.utils, os
from webnotes.modules.export_file import export_to_files

def execute():
	webnotes.reload_doc("core", "doctype", "file_data")
	webnotes.reset_perms("File Data")
	
	singles = get_single_doctypes()
	
	for doctype in webnotes.conn.sql_list("""select parent from tabDocField where 
		fieldname='file_list'"""):
		update_file_list(doctype, singles)
		
		webnotes.conn.sql("""delete from tabDocField where fieldname='file_list'
				and parent=%s""", doctype)
		
		# export_to_files([["DocType", doctype]])
		
def get_single_doctypes():
	return webnotes.conn.sql_list("""select name from tabDocType
			where ifnull(issingle,0)=1""")
		
def update_file_list(doctype, singles):
	if doctype in singles:
		doc = webnotes.doc(doctype, doctype)
		if doc.file_list:
			update_for_doc(doctype, doc)
			webnotes.conn.set_value(doctype, None, "file_list", None)
	else:
		try:
			for doc in webnotes.conn.sql("""select name, file_list from `tab%s` where 
				ifnull(file_list, '')!=''""" % doctype, as_dict=True):
				update_for_doc(doctype, doc)
			webnotes.conn.commit()
			webnotes.conn.sql("""alter table `tab%s` drop column `file_list`""" % doctype)
		except Exception, e:
			print webnotes.getTraceback()
			if (e.args and e.args[0]!=1054) or not e.args:
				raise e

def update_for_doc(doctype, doc):
	for filedata in doc.file_list.split("\n"):
		if not filedata:
			continue
			
		filedata = filedata.split(",")
		if len(filedata)==2:
			filename, fileid = filedata[0], filedata[1] 
		else:
			continue
		
		exists = True
		if not (filename.startswith("http://") or filename.startswith("https://")):
			if not os.path.exists(webnotes.utils.get_path("public", "files", filename)):
				exists = False

		if exists:
			if webnotes.conn.exists("File Data", fileid):
				fd = webnotes.bean("File Data", fileid)
				if not (fd.doc.attached_to_doctype and fd.doc.attached_to_name):
					fd.doc.attached_to_doctype = doctype
					fd.doc.attached_to_name = doc.name
					fd.save()
				else:
					try:
						fd = webnotes.bean("File Data", copy=fd.doclist)
						fd.doc.attached_to_doctype = doctype
						fd.doc.attached_to_name = doc.name
						fd.doc.name = None
						fd.insert()
					except webnotes.DuplicateEntryError:
						pass
		else:
			webnotes.conn.sql("""delete from `tabFile Data` where name=%s""",
				fileid)