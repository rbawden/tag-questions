from readfile import *
from classify_tag_questions import *
from utils import *
import os, re


def read_tagfiles(tagtype, langpair, fol, dataset, baseline=False):
    if tagtype == "tagnottag":
        tags = read_lines(fol+"/en_tag_questions."+dataset+"."+"list."+langpair)
        return tags
    else:
        gramtags = read_lines(fol+"/en_tag_questions_gram."+dataset+"."+"list."+langpair)
        pospos = read_lines(fol+"/en_tag_questions_gram-postag-posanchor."+dataset+"."+"list."+langpair)
        negneg = read_lines(fol+"/en_tag_questions_gram-negtag-neganchor."+dataset+"."+"list."+langpair)
        negpos = read_lines(fol+"/en_tag_questions_gram-postag-neganchor."+dataset+"."+"list."+langpair)
        posneg = read_lines(fol+"/en_tag_questions_gram-negtag-posanchor."+dataset+"."+"list."+langpair)
        if tagtype == "fine":
            misctags = read_lines(fol+"/en_tag_questions_misc."+dataset+"."+"list."+langpair)
            return gramtags, pospos, negneg, negpos, posneg, misctags
        elif tagtype == "finer":
            miscposanchor = read_lines(fol+"/en_tag_questions_misc-posanchor."+dataset+"."+"list."+langpair)
            miscneganchor = read_lines(fol+"/en_tag_questions_misc-neganchor."+dataset+"."+"list."+langpair)
            return gramtags, pospos, negneg, negpos, posneg, miscposanchor, miscneganchor
        elif tagtype in ["gramMiscNone", "gramMiscTypeNone"]:
            gramtags = read_lines(fol+"/en_tag_questions_gram."+dataset+"."+"list."+langpair)
            misctags = read_lines(fol+"/en_tag_questions_misc."+dataset+"."+"list."+langpair)
            return gramtags, misctags
        else:
            exit("Tag type not recognised in "+read_tagfiles.__name__+"\n")

# get 3 main types (gram, misc and none)
def get_gramMiscNone(dataset, sourcefile, line_folder, langpair, tagtype, baseline=False):
    gramtags, misctags = read_tagfiles(tagtype, langpair, line_folder,
                                       dataset)

    if ".gz" in sourcefile: sp = gzip.open(sourcefile, "rt", encoding="utf-8")
    else: sp = open(sourcefile, "r", encoding="utf-8")
    
    for i, line in enumerate(sp.readlines()):
        if binary_search(i+1, gramtags): os.sys.stdout.write("gram\n")
        elif binary_search(i+1, misctags): os.sys.stdout.write("misc\n")
        else: os.sys.stdout.write("none\n")
    sp.close()

def get_gramMiscTypesNone(dataset, sourcefile, line_folder, langpair, tagtype, baseline=False):
    gramtags, misctags = read_tagfiles(tagtype, langpair, line_folder,
                                       dataset)

    if ".gz" in sourcefile: sp = gzip.open(sourcefile, "rt", encoding="utf-8")
    else: sp = open(sourcefile, "r", encoding="utf-8")
    
    for i, line in enumerate(sp.readlines()):

        # baseline
        if baseline:
            if is_en_tag(line):
                # os.sys.stderr.write(line+"\n")
                anchor, tag = get_anchor_and_tag(line.strip())
                # os.sys.stderr.write(str(anchor)+" "+str(tag)+"\n")
                tag = re.sub("(^["+get_punct()+"]+|["+get_punct()+" ]+$)", "", tag).lower()
            else:
                tag = "none"

            if is_en_gram_tag(line):
                tag = "gram"

            # correct okay -> ok
            if tag.strip()=="okay": tag="ok"
                
            os.sys.stdout.write(tag.strip().replace(" ", "_").replace("'", "-")+"\n")

        # gold labels
        else:
            if binary_search(i+1, gramtags): os.sys.stdout.write("gram\n")
            elif binary_search(i+1, misctags):
                anchor, tag = get_anchor_and_tag(line.strip())
                if tag: tag = re.sub("(^["+get_punct()+"]+|["+get_punct()+" ]+$)", "", tag).lower()
                else: tag="none"
                # change okay
                if tag.strip()=="okay": tag="ok"

                if tag=="okay":
                    exit("aargh")
                
                os.sys.stdout.write(tag.strip().replace(" ", "_").replace("'", "-")+"\n")
            else: os.sys.stdout.write("none\n")
    sp.close()

             
# get finer labels (all polarites, excl. misc) for a given input file
def get_fine(dataset, sourcefile, line_folder, langpair, tagtype, baseline=False):
    gramtags, pospos, negneg, negpos, posneg, misctags = read_tagfiles(tagtype, langpair)
    with open(sourcefile) as sp:
        for i, line in enumerate(sp.readlines()):
            if binary_search(i+1, pospos): os.sys.stdout.write("gram_pospos\n")
            elif binary_search(i+1, posneg): os.sys.stdout.write("gram_posneg\n")
            elif binary_search(i+1, negpos): os.sys.stdout.write("gram_negpos\n")
            elif binary_search(i+1, negneg): os.sys.stdout.write("gram_negneg\n")
            elif binary_search(i+1, misctags): os.sys.stdout.write("misc\n")
            else: os.sys.stdout.write("none\n")

# get finer labels (all polarites, incl. misc) for a given input file
def get_finer(dataset, sourcefile, line_folder, langpair, tagtype, baseline=False):
    gramtags, pospos, negneg, negpos, posneg, miscposanchor, miscneganchor = read_tagfiles(tagtype, langpair)
    with open(sourcefile) as sp:
        for i, line in enumerate(sp.readlines()):
            if binary_search(i+1, pospos): os.sys.stdout.write("gram_pospos\n")
            elif binary_search(i+1, posneg): os.sys.stdout.write("gram_posneg\n")
            elif binary_search(i+1, negpos): os.sys.stdout.write("gram_negpos\n")
            elif binary_search(i+1, negneg): os.sys.stdout.write("gram_negneg\n")
            elif binary_search(i+1, miscposanchor): os.sys.stdout.write("misc_pos\n")
            elif binary_search(i+1, miscneganchor): os.sys.stdout.write("misc_neg\n")
            else: os.sys.stdout.write("none\n")

# get real labels (question tag form) for a given input file
def get_real(dataset, sourcefile, line_folder, langpair, tagtype, baseline=False):
    tags = read_lines(line_folder+"/en_tag_questions."+dataset+".list."+langpair)
    if not os.path.exists(sourcefile) and ".gz" not in sourcefile: sourcefile+=".gz" # try .gz file
    elif not os.path.exists(sourcefile) and ".gz" in sourcefile: sourcefile = sourcefile.replace(".gz", "")
    if ".gz" in sourcefile: sp = gzip.open(sourcefile, "rt")
    else: sp = open(sourcefile, "r", encoding="utf-8")
        
    for i, line in enumerate(sp):
        # os.sys.stderr.write(str(i)+":"+line)
        if line.strip()=="" and not baseline: break
        # baseline
        if baseline:
            if is_en_tag(line):
                # os.sys.stderr.write(line+"\n")
                anchor, tag = get_anchor_and_tag(line.strip())
                # os.sys.stderr.write(str(anchor)+" "+str(tag)+"\n")
                if tag: tag = re.sub("(^["+get_punct()+"]+|["+get_punct()+" ]+$)", "", tag).lower()
                else: tag="none"
            else: tag="none"

            # correct okay -> ok
            if tag.strip()=="okay": tag="ok"
                
            os.sys.stdout.write(tag.strip().replace(" ", "_").replace("'", "-")+"\n")

        else:
            if binary_search(i+1, tags):
                line = retokenise(line) # very important!
                # os.sys.stderr.write(str(i+1)+"\n")
                anchor, tag = get_anchor_and_tag(line.strip())
                if tag: tag = re.sub("(^["+get_punct()+"]+|["+get_punct()+" ]+$)", "", tag).lower()
                # os.sys.stderr.write(tag+"\n")
            else: tag="none"

            # correct okay -> ok
            if tag.strip()=="okay": tag="ok"
            
            os.sys.stdout.write(tag.strip().replace(" ", "_").replace("'", "-")+"\n")
    # if tags[-1]> i: exit("The source file is too short compared to the subcorpora file")
    sp.close()
                
# get gold labels True or False for a given input file
def get_tagnottag(dataset, sourcefile, line_folder, langpair, tagtype, baseline=False):
    tags = read_lines(line_folder+"/en_tag_questions."+dataset+"."+"list."+langpair)
    if not os.path.exists(sourcefile) and ".gz" not in sourcefile: sourcefile+=".gz" # try .gz file
    elif not os.path.exists(sourcefile) and ".gz" in sourcefile: sourcefile = sourcefile.replace(".gz", "")
    if ".gz" in sourcefile: sp = gzip.open(sourcefile, "rt", encoding="utf-8")
    else: sp = open(sourcefile, "r", encoding="utf-8")
        
    for i, line in enumerate(sp.readlines()):
        if baseline:
            if is_en_tag(line):
                os.sys.stdout.write("True\n")
            else:
                os.sys.stdout.write("False\n")
        else:
            if binary_search(i+1, tags): os.sys.stdout.write("True\n")
            else: os.sys.stdout.write("False\n")

    sp.close()

        
if __name__=="__main__":                
    import argparse
    argparser = argparse.ArgumentParser()
    argparser.add_argument("dataset", choices=("train", "dev1", "dev2", "test"))
    argparser.add_argument("langpair", choices=("cs-en", "fr-en", "de-en", "fr2000-en2000", "de2000-en2000", "cs2000-en2000"))
    argparser.add_argument("tagtype", choices=("real", "tagnottag", "gramMiscNone", "gramMiscTypeNone"))
    argparser.add_argument("linenumber_folder", help="the folder containing line files")
    argparser.add_argument("sourcefile", help="the English text source file")
    argparser.add_argument("-baseline", action='store_true', default=False)
    args = argparser.parse_args()

    if args.linenumber_folder[-1] == "/": args.linenumber_folder = args.linenumber_folder[:-1]
    if args.tagtype == "real": get_function = get_real
    elif args.tagtype == "tagnottag": get_function = get_tagnottag
    elif args.tagtype == "gramMiscNone": get_function = get_gramMiscNone
    elif args.tagtype == "gramMiscTypeNone": get_function = get_gramMiscTypesNone

    get_function(args.dataset, args.sourcefile, args.linenumber_folder, args.langpair, args.tagtype, args.baseline)
    
                
