import base64


from PyPDF2 import PdfFileWriter, PdfFileReader
from io import StringIO
from dateutil.parser import parse
import re

import pandas as pd
import camelot


re_acc_basis1 = '(MODIFIED ACCRUAL|MODIFIED CASH|REGULATORY|ACCRUAL|CASH) BASIS OF ACCOUNTING'
#re_acc_basis2 = '(ACCRUAL|CASH|REGULATORY) BASIS OF ACCOUNTING'
Accounting_Basis = ''
basis_count = 0
bal_sht_1 = ['Cash']
bal_sht_2 = ['Cash and Demand Accounts','Cash and investments','Cash and deposits','Cash and time deposits']
bal_sht_3 = ['cash and equivalents','Cash in county Treasury','Cash in Revolving Fund','Cash on Hand','Cash in Banks','Collection Awaiting Deposit','non-pooled cash, petty cash, pooled cash','demand deposit','Demand Accounts','equity in cash and investments','equity in Pooled Cash and Cash Equivalents']
bal_sht_1 = [x.upper() for x in bal_sht_1]
bal_sht_2 = [x.upper() for x in bal_sht_2]
bal_sht_3 = [x.upper() for x in bal_sht_3]

#filename = "Englewood_2017.pdf"
#filename = "Calhoun,GA_2017.pdf"

def decrypt_pdf(input_path, output_path, password):
	with open(input_path, 'rb') as input_file,open(output_path, 'wb') as output_file:
		reader = PdfFileReader(input_file)
		reader.decrypt(password)

		writer = PdfFileWriter()

		for i in range(reader.getNumPages()):
		  writer.addPage(reader.getPage(i))

		writer.write(output_file)

def get_acc_basis(filename):
	inputpdf = PdfFileReader(open(filename, "rb"))
	if inputpdf.isEncrypted:
		#decrypt_pdf(filename,filename+'_2','')
		#inputpdf = PdfFileReader(open(filename.split('/')[1]+'_2', "rb"))
		pass


	for page in range(0,inputpdf.numPages):
		#pdf_page_contents = inputpdf.getPage(page).extractText().upper().encode('ascii','ignore')
		#print(page)
		pdf_page_contents = inputpdf.getPage(page).extractText().upper()
		#print(type(pdf_page_contents))
		basis = "BASIS OF ACCOUNTING"
		status = re.findall(basis,pdf_page_contents)
		# print status

		if status != [] and basis_count==0:
			#print("found!!!!------------------------------- basis of accounting")
			#print(status)
			match1 = re.findall(re_acc_basis1,pdf_page_contents)
			if match1 != []:
				basis_count+=1
				Accounting_Basis = match1[0]
			pass
			#print(Accounting_Basis)
			
	mapng = {'MODIFIED ACCRUAL': 'Modified Accrual', 'MODIFIED CASH':'Modified Cash', 'REGULATORY': 'Regulatory', 'ACCRUAL':'Accrual','CASH' : 'Cash'}
	if Accounting_Basis in mapng.keys():
		return mapng[Accounting_Basis]
	else:
		return 'na' 
	
	return 'na'

def get_Cash_Amt(filename):	   
	inputpdf = PdfFileReader(open(filename, "rb"))
	for page in range(0,inputpdf.numPages):
		#pdf_page_contents = inputpdf.getPage(page).extractText().upper().encode('ascii','ignore')
		#print(page)
		pdf_page_contents = inputpdf.getPage(page).extractText().upper()
		status = []

		tablesearch = "BALANCE SHEET GOVERNMENTAL FUNDS|BALANCE SHEET\nGOVERNMENTAL FUNDS"
		status = re.findall(tablesearch,pdf_page_contents)
		# print status

		if status != []:
			#print("found!!!!------------------------------- {}".format(page))
			#print(status)
			# print pdf_page_contents
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

			for idx,row in df[0].df.iterrows():
				# print idx
				# print row
				if row['fullrow'].upper() in ["BALANCE SHEET","BALANCE SHEET GOVERNMENTAL FUNDS","GOVERNMENTAL FUNDS"]:
					#print("junk row found")
					rows_to_delete.append(idx)

				try:
					parse(row['fullrow'])
					rows_to_delete.append(idx)
				except Exception as e:
					pass

			del df[0].df['fullrow']

			rows_to_delete = list(set(rows_to_delete))
			df[0].df= df[0].df.drop(rows_to_delete)	

			print(df[0].df)

			newdf = df[0].df

			newdf.index = newdf[0]
			#newdf.to_csv(filename.split(".pdf")[0]+"_govtbalances_preT.csv",index=False)
			#print(newdf.columns)
			col_to_consider = []
			for col in newdf.columns:
				#print(col)
				#print(len(newdf[col].unique()))
				if len(newdf[col].unique())>3:
					col_to_consider.append(col)
			fin_df = newdf[col_to_consider[0:2]]
		
			#fin_df2 = pd.DataFrame():
			fin_df.index = range(len(fin_df))
			#print(fin_df)
			#print(fin_df.columns)
			first_col = fin_df.columns[0]
			sec_col = fin_df.columns[1]
			#print(len(fin_df))
			#fin_df = fin_df[pd.notnull(fin_df[first_col])]
			fin_df = fin_df[fin_df[first_col]!='']
			fin_df = fin_df[fin_df[sec_col]!='']
			#print(len(fin_df))
			#print(fin_df.columns)
			fin_df[first_col] = fin_df[first_col].apply(lambda x:x.upper())
			amount = 0
			if 'CASH' in fin_df[first_col].tolist():
				ser = fin_df[fin_df[first_col] == 'CASH']
				#print(ser)
				amount += int(ser[sec_col].sum())
			else:
				for cash_col in bal_sht_2:
					print(cash_col)
					ser = fin_df[fin_df[first_col] == cash_col]
					print(ser)
					amount += int(ser[sec_col].sum())
			
			for cash_col in bal_sht_3:
				print(cash_col)
				ser = fin_df[fin_df[first_col] == cash_col]
				print(ser)
				amount += int(ser[sec_col].sum())
			
			return amount
		
	
	return 0


#get_acc_basis('Test Data/Stone County_MO_326056_G O Municipality & County_County_2016.pdf')


from os import listdir
from os.path import isfile, join	
	
result_df = pd.read_csv('results.csv')

dirname = 'Test Data'

allfiles = [f for f in listdir('Test Data') if isfile(join(dirname, f))]
#print(allfiles)

Mapped_names = [x.split('_')[0]+'_'+x.split('_')[1]+'_'+x.split('_')[2] for x in allfiles]
#print(Mapped_names)
Mapped_names = [x.upper() for x in Mapped_names]

for val in Mapped_names:
	if(val == 'HIDALGO CNTY DR DIST 1_TX_7635'):
		ind = Mapped_names.index(val)
		Mapped_names[ind] = 'HIDALGO CNTY DR DIST #1_TX_7635'
	
	
result_df['Credit Name'] = result_df['Credit Name'].apply(lambda x : x.strip())
result_df['State'] = result_df['State'].apply(lambda x : x.strip())
result_df['Key'] = result_df['Credit Name']+'_'+result_df['State']+'_'+result_df['Org ID'].astype(str)

result_df['Key'] = result_df['Key'].apply(lambda  x:x.upper())

result_df['Mapped_fname'] = result_df['Key'].apply(lambda x:allfiles[Mapped_names.index(x)])


result_df['Pension Plan 1 Name'] = 'Not Found'
result_df['Pension Plan 1 Measurement Date'] = 'No Date'
result_df['Pension Plan 1 Total Pension Liability'] = 0
result_df['Pension Plan 2 Name'] = 'Not Found'
result_df['Pension Plan 2 Measurement Date'] = 'No Date'
result_df['Pension Plan 2 Total Pension Liability'] = 0
result_df['Balance Sheet Cash'] = 0
result_df['Accounting Basis'] = 'na'


#result_df=result_df[0:2]

#result_df['Accounting Basis'] = result_df['Mapped_fname'].apply(lambda x: get_acc_basis('Test Data/'+x))

'''for id, row in result_df.iterrows():
	print('Test Data/'+row['Mapped_fname'])
	bas = 'na'
	try:
		bas = get_acc_basis('Test Data/'+row['Mapped_fname'])
	except Exception as e:
		print(e)
	result_df.at[id,'Accounting Basis'] = bas
	print(bas)
'''

for id, row in result_df.iterrows():
	print('Test Data/'+row['Mapped_fname'])
	cash_amt = 0
	try:
		cash_amt = get_Cash_Amt('Test Data/'+row['Mapped_fname'])
	except Exception as e:
		print(e)
	result_df.at[id,'Balance Sheet Cash'] = cash_amt
	print(cash_amt)


result_df.to_csv('res2.csv',index=False)

