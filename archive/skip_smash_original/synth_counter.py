import os

for dir in os.listdir():
	s = 0
	if os.path.isdir(dir) == True:
		acc = str(dir)
		os.chdir(dir)
		for f in os.listdir():
			if f.endswith("_upstream.fasta"):
				with open(f,"r") as up:
					for line in up:
						if "synthase" in line:
							s += 1
			if f.endswith("_downstream.fasta"):
				with open(f,"r") as down:
					for line in down:
						if "synthase" in line:
							s += 1
		os. chdir("..")
		with open("synth_counts.csv","a+") as o:
			o.write(acc+","+str(s))
			o.write("\n")


