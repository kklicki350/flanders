import os

with open("genomes.txt","w") as g:
	for d in os.listdir():
		if d.isdir():
			g.write(d)
			g.write("\n")
		else:
			pass
