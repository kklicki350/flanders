import os

for dir in os.listdir():
	s = 0
	if os.path.isdir(dir) == True:
		acc = str(dir)
		os.chdir(dir)
		for f in os.listdir():
			if f.endswith("_upstream.fasta"):
				with open(f,"r") as up:
					ups = []
					for line in up:
						if line.startswith(">"):
							annotation = line[line.find(".")+2:line.find("[")].strip()
							ups.append(annotation)
			if f.endswith("_downstream.fasta"):
				with open(f,"r") as down:
					downs=[]
					for line in down:
						if line.startswith(">"):
							annotation = line[line.find(".")+2:line.find("[")].strip()
							downs.append(annotation)
		os. chdir("..")
		with open("full_annotations.tsv","a+") as o:
			o.write(acc+"\t"+str(ups).lstrip("[").rstrip("]")+"\t"+str(downs).lstrip("[").rstrip("]"))
			o.write("\n")
