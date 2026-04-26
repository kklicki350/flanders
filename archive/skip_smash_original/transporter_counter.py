import os

t_list=["Transport","transport","Transporter","transporter","ABC","MFS","Permease","permease","Translocase","translocase"]
for dir in os.listdir():
	s = 0
	if os.path.isdir(dir) == True:
		acc = str(dir)
		os.chdir(dir)
		for f in os.listdir():
			if f.endswith("_upstream.fasta"):
				with open(f,"r") as up:
					for line in up:	
						if any(s in line for s in t_list) == True:
							s += 1
			if f.endswith("_downstream.fasta"):
				with open(f,"r") as down:
					for line in down:
						if any(s in line for s in t_list) == True:
							s += 1
		os. chdir("..")
		with open("transporter_counts.csv","a+") as o:
			o.write(acc+","+str(s))
			o.write("\n")



