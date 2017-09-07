# recalculate film lines after removal of blank lines
import argparse
import gzip
import os

argparser=argparse.ArgumentParser()
argparser.add_argument('filmlines_file')
argparser.add_argument('removed_lines_file')
args = argparser.parse_args()

filmlines = []
if ".gz" in args.filmlines_file: fl = gzip.open(args.filmlines_file, "rt")
else: fl = open(args.filmlines_file, "rt")
for line in fl:
    line = line.strip("\n")
    filminfo = line.split("\t")
    for i in range(len(filminfo)):
        if i < 3: filminfo[i] = int(filminfo[i])
        else: filminfo[i] = str(filminfo[i])
    filmlines.append(filminfo)
fl.close()
    
removed = []
if ".gz" in args.removed_lines_file: rl = gzip.open(args.removed_lines_file, "rt")
else: rl = open(args.removed_lines_file, "rt")
    
for line in rl:
    removed.append(int(line.strip()))
rl.close()

# modify film lines
previously_removed = 0
for filminfo in filmlines:
    start, end = filminfo[1], filminfo[2]
    num_removed = len([x for x in removed if x >= start and x <=end])
    removed = removed[num_removed:]
    
    if num_removed == end-start:
        os.sys.stderr.write("film "+str(filminfo[0])+" deleted\n")
    else:
        os.sys.stdout.write(str(filminfo[0])+"\t"+str(start-previously_removed)+"\t"+str(end-previously_removed-num_removed)+"\t"+"\t".join(filminfo[3:])+"\n")

    previously_removed += num_removed
    



        
