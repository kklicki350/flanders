import os
import pandas as pd
import csv

master_csv = pd.DataFrame(columns=["Genome","Location","Accessions","BGC_Type","Signal_peptide","Signal_peptide_count","Clusterblast_hits"])

for d in os.listdir():
	if "." in d:
		continue
		print(d)
	else:
		os.chdir(d)
		c = pd.DataFrame()
		for f in os.listdir(d):
			if f.endswith(".tsv"):
				c = pd.read_csv(f,index_col=None, header=0,sep="\t")
				for r in c.iterrows():
					print(r)
				master_csv = pd.concat([master_csv,c],axis=0)
				for l in master_csv.iterrows():
					print(l)
			else:
				continue
		os.chdir("..")
for q in master_csv.iterrows():
	print(q)
with open(output.txt,"a+") as o:
	for r in master_csv.iterrows():
		o.write(r)