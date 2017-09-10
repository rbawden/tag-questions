import argparse, os, re, gzip
from classify_tag_questions2 import get_anchor_and_tag, is_en_tag



def get_final_translation(transfile, predfile):
    diff=0

    # transfile
    # if not os.path.exists(transfile) and ".gz" not in transfile: transfile+=".gz" # try .gz file
    # elif not os.path.exists(transfile) and ".gz" in transfile: transfile = transfile.replace(".gz", "")
    if ".gz" in transfile: tf = gzip.open(transfile, "rt")
    else:  tf = open(transfile, "r")

    # predfile
    # if not os.path.exists(predfile) and ".gz" not in predfile: predfile+=".gz" # try .gz file
    # elif not os.path.exists(predfile) and ".gz" in predfile: predfile = predfile.replace(".gz", "")
    if ".gz" in predfile: pf = gzip.open(predfile, "rt")
    else:  pf = open(predfile, "r")
        
    for i, (t, p) in enumerate(zip(tf, pf)):
        t = t.strip()
        p = p.strip()
        p = p.replace("_", " ").replace("-", "'")

        if p=="okay": p=="ok"
        t = re.sub("(^| |[\-\'])okay", r"\1ok", t)

        # if "unwanted attention" in t:
        # os.sys.stderr.write(t+"\n")
        # os.sys.stderr.write(p+"\n")

        # add newline
        # if i!=0: os.sys.stdout.write("\n")
        
        if p=="none":
            os.sys.stdout.write(t+"\n")
        else:
            # remove old tag if there was one...
            if is_en_tag(t):
                anchor, tag = get_anchor_and_tag(t)
                anchor = re.sub("[\.\,\!\?\"\' ]+$", "", anchor)
                os.sys.stdout.write(anchor.strip()+" , "+p+" ?\n")
                # print(t)
                # input()
            elif re.match(".*? \, (or|ne|wa) \?$", t):
                anchor = re.match(".*? \, (or|ne|wa) \?$", t).group(1)
                os.sys.stdout.write(anchor.strip()+" , "+p+" ?\n")
            else:
                t = re.sub("[\.\,\!\?\"\' ]+$", "", t)
                os.sys.stdout.write(t.strip()+" , "+p+" ?\n")

    tf.close()
    pf.close()


if __name__=="__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("trans_file")
    argparser.add_argument("predictions")
    args = argparser.parse_args()
    
    get_final_translation(args.trans_file, args.predictions)
