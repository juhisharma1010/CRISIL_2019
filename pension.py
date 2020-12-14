import base64


from PyPDF2 import PdfFileWriter, PdfFileReader
from io import StringIO
from dateutil.parser import parse
import re
import pandas as pd
import camelot

filename = "Englewood_2017.pdf"
#filename = "Calhoun,GA_2017.pdf"

inputpdf = PdfFileReader(open(filename, "rb"))

for page in range(0,inputpdf.numPages):
	#pdf_page_contents = inputpdf.getPage(page).extractText().upper().encode('ascii','ignore')
	#print(page)
	pdf_page_contents = inputpdf.getPage(page).extractText().upper()
	#print(type(pdf_page_contents))

	tablesearch = "SCHEDULE OF CHANGES IN THE NET PENSION LIABILITY"
	status = re.findall(tablesearch,pdf_page_contents)
	# print status
	all_names = []
	all_amt = []
	if status != []:
		print(page)
		#print('found_net_table')
		df = camelot.read_pdf(filename,pages=str(page+1),flavor='stream')
		#print(df)
		#print(df[0].df.iloc[0])
		rows_to_delete = []
		df[0].df = df[0].df.applymap(str)
		df[0].df = df[0].df.applymap(lambda x: x.replace("\n",""))
		df[0].df = df[0].df.applymap(lambda x: x.replace(":",""))
		df[0].df = df[0].df.applymap(lambda x: x.replace("$",""))
		df[0].df = df[0].df.applymap(lambda x: x.replace(",",""))
		df[0].df = df[0].df.applymap(lambda x: re.sub(r"[\\]+n","",x))
		df[0].df = df[0].df.applymap(lambda x: re.sub(r"[\\]+t","",x))
		df[0].df = df[0].df.applymap(lambda x: re.sub(r"[\\]+r","",x))
		df[0].df = df[0].df.applymap(lambda x: re.sub(r"  +","",x))
		df[0].df = df[0].df.applymap(str.strip)
		df[0].df['fullrow'] = df[0].df.values.sum(axis=1)
		df[0].df['fullrow'] =df[0].df['fullrow'].apply(str)
		#print(df[0].df)
		
		id_sc = 0
		get_this_table = False
		for idx,row in df[0].df.iterrows():
			# print idx
			# print row
			st2 = re.findall('(SCHEDULE OF.{,10}CHANGES.{,15}NET PENSION LIABILITY)',row['fullrow'].upper())
			if st2:
				print("junk row found")
				get_this_table = True
				rows_to_delete.append(idx)

			try:
				parse(row['fullrow'])
				rows_to_delete.append(idx)
			except Exception as e:
				pass
		
		if get_this_table:
			#print(df[0].df['fullrow'])
			full_r = df[0].df['fullrow']
			all_names.append(full_r.tolist()[1])
			del df[0].df['fullrow']
			rows_to_delete = list(set(rows_to_delete))
			df[0].df= df[0].df.drop(rows_to_delete)	

			#print(df[0].df)

			newdf = df[0].df
			
			#newdf.to_csv('newdf.csv')
			
			temp_df = newdf[newdf[0]=='Total pension liability--ending']
			try:
				temp_df[1] = temp_df[1].apply(lambda x:int(x))
				print(sum(temp_df[1]))
				y = sum(temp_df[1])
				all_amt.append(y)
			except e:
				all_amt.append(0)
				pass
                
    print(all_amt,all_names)