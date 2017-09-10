#!/usr/bin/python3
import csv, argparse
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import numpy as np
import itertools

# read tab-separated file containing manual annotations of large coverage
# grammatical tag question candidates. Columns=line number, text, tag, not tag,
# mid-utterance tag, no anchor in subtitle
def read_annotated(filename):
    subs = []
    with open(filename, "r") as fp:
        reader = csv.reader(fp, delimiter="\t", quoting=csv.QUOTE_NONE)
        for i, line in enumerate(reader):
            if i==0: continue # ignore headers
            if "".join(line).strip()=="": break # end of file    
            for i in range(len(line)):
                line[i] = line[i].strip()
                if i in [2, 3, 7]:
                    if line[i]=="x": line[i] = True
                    else: line[i] = False
            line[0] = int(line[0])
            subs.append(line)

    return subs

# read the file containing the list of lines automatically identified as tag
# questions
def read_lines(filename):
    lines = []
    with open(filename, "r") as fp:
        for line in fp:
            lines.append(int(line.strip()))
    return lines


def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    """
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, cm[i, j],
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    

# compare the lines present in the manually annotated file with what was found
# in the automatic evaluation
def evaluate(manual, tags, postags, negtags, posanchors, neganchors, pospos, \
             negneg, posneg, negpos):

    tagsfound, tagsnotfound, tagsfalsepositive = [], [], []
    posfound, posnotfound, negfound, negnotfound = [], [], [], []
    posfalsepositive, negfalsepositive = [], []
    posanchorfound, posanchornotfound, neganchorfound,neganchornotfound = [], [], [], []
    posanchorfalsepositive, neganchorfalsepositive = [], []    
    posposfound, posposnotfound, negnegfound, negnegnotfound = [], [], [], []
    posnegfound, posnegnotfound, negposfound, negposnotfound = [], [], [], []
    posposfalsepositive, posnegfalsepositive, negnegfalsepositive, negposfalsepositive = [], [], [], []


    # shortcuts for indices of list
    num, text, tag, nottag, polarityanchor, polaritytag, senttype, elidsubj= 0,1,2,3,4,5,6,7

    # for confusion matrix for finest grain labels
    y_true = []
    y_pred = []
    
    for line in manual:

        #------------------------------------------------------------
        # 1) Is the utterance a tag question? (primary identification)
        if line[tag]:
            if line[num] in tags: tagsfound.append(line)
            else: tagsnotfound.append(line)
        if line[nottag]:
            if line[num] in tags: tagsfalsepositive.append(line)

        if not line[tag]: continue # do not continue if it is not a tag
        #------------------------------------------------------------
        # 2) Of those correctly identified as tag questions, are the polarity
        # labels correctly assigned?

        # 2.1) question tag polarity
        if line[polaritytag]=="pos":
            if line[num] in postags: posfound.append(line)
            else: posnotfound.append(line)
        if line[polaritytag]=="neg":
            if line[num] in negtags: negfound.append(line)
            else: negnotfound.append(line)       
        if line[polaritytag]!="pos" and line[num] in postags:
            posfalsepositive.append(line)
        if line[polaritytag]!="neg" and line[num] in negtags:
            negfalsepositive.append(line)

        # 2.2) anchor polarity
        if line[polarityanchor]=="pos":
            if line[num] in posanchors: posanchorfound.append(line)
            else: posanchornotfound.append(line)
        if line[polarityanchor]=="neg":
            if line[num] in neganchors: neganchorfound.append(line)
            else: neganchornotfound.append(line)
        if line[polarityanchor]!="pos" and line[num] in posanchors:
            posanchorfalsepositive.append(line)
        if line[polarityanchor]!="neg" and line[num] in neganchors:
            neganchorfalsepositive.append(line)

        # 3.3) tag and anchor polarity
        
        # for the confusion matrix
        y_true.append(line[polarityanchor]+"anchor-"+line[polaritytag]+"tag")
        if line[num] in pospos: y_pred.append("posanchor-postag")
        elif line[num] in posneg: y_pred.append("posanchor-negtag")
        elif line[num] in negneg: y_pred.append("neganchor-negtag")
        elif line[num] in negpos: y_pred.append("neganchor-postag")

        
        # those annotated as (pos anchor, pos tag)
        if line[polaritytag]=="pos" and line[polarityanchor]=="pos":
            if line[num] in pospos: posposfound.append(line)
            else: posposnotfound.append(line)

        # those annotated as (neg anchor, pos tag)
        if line[polaritytag]=="pos" and line[polarityanchor]=="neg":
            if line[num] in negpos: negposfound.append(line)
            else: negposnotfound.append(line)

        # those annotated as (neg anchor, neg tag)
        if line[polaritytag]=="neg" and line[polarityanchor]=="neg":
            if line[num] in negneg: negnegfound.append(line)
            else: negnegnotfound.append(line)

        # those annotated as (pos anchor, neg tag)
        if line[polaritytag]=="neg" and line[polarityanchor]=="pos":
            if line[num] in posneg: posnegfound.append(line)
            else: posnegnotfound.append(line)
                
        # false positives
        if y_true[-1] != "posanchor-postag" and line[num] in pospos:
            posposfalsepositive.append(line)
        elif y_true[-1] != "posanchor-negtag" and line[num] in posneg:
            posnegfalsepositive.append(line)
        elif y_true[-1] != "neganchor-negtag" and line[num] in negneg:
            negnegfalsepositive.append(line)
        elif y_true[-1] != "neganchor-postag" and line[num] in negpos:
            negposfalsepositive.append(line)
        

    #------------------------------------------------------------
    # print out some results
    types = [("Grammatical TQ", tagsfound, tagsnotfound, tagsfalsepositive, tags),
             ("Pos tag", posfound, posnotfound, posfalsepositive, postags),
             ("Neg tag", negfound, negnotfound, negfalsepositive, negtags),
             ("Pos anchor", posanchorfound, posanchornotfound, posanchorfalsepositive, posanchors),
             ("Neg anchor", neganchorfound, neganchornotfound, neganchorfalsepositive, neganchors),
             ("Positive tag, positive anchor", posposfound, posposnotfound, posposfalsepositive, pospos),
             ("Negative tag, negative anchor", negnegfound, negnegnotfound, negnegfalsepositive, negneg),
             ("Negative tag, positive anchor", posnegfound, posnegnotfound, posnegfalsepositive, negpos),
             ("Positive tag, negative anchor", negposfound, negposnotfound, negposfalsepositive, posneg)]

    print("\n")
    correct = 0
    for tt in types:
        
        num = len(tt[1]) # number of automatic tags found
        total =  (num+len(tt[3])) # total number classed as this TQ type automatically
        manualtotal = (num+len(tt[2]))
        if total==0: percent= "undef"
        else: percent = round((num*100)/total,2)
        if manualtotal==0: percentrecall="undef"
        else: percentrecall = round((num*100)/manualtotal,2)
        fp = len(tt[3])
        allfound = fp+num
        if num!=0: fppercent = round((100*fp)/allfound,2)

        if "tag" in tt[0] and "anchor" in tt[0]:
            correct+=num
            
        print(tt[0]+": Precision: "+str(num)+"/"+str(total)+" ("+str(percent)+"%) correct")
        print("\tFalse positives in automatic extraction = "+str(fp)+" ("+str(fppercent)+"%)")
        print("\tRecall: "+str(num)+"/"+str(manualtotal)+" ("+str(percentrecall)+"%) found\n")

    print("Overall precision for 4 polarity types = "+str(correct)+"/"+str(len(tagsfound))+" ("+str(round(100*correct/float(len(tagsfound)),2))+"%)")
    #------------------------------------------------------------


    # confusion matrix
    classes = ["neganchor-negtag", "neganchor-postag", "posanchor-negtag", "posanchor-postag"]
    cm = confusion_matrix(y_true, y_pred)
    plt.figure()

    print(set(y_true))
    print(set(y_pred))
    print(cm)
   
    plot_confusion_matrix(cm, classes, title='Identification of tag question polarities')
    plt.show()
    
    #return
            
    print("Incorrectly annotated=")
    for inc in negfalsepositive:
        print(inc[1])
        #linenum = inc[0]
        # if inc in True:#posfalsepositive:
            # print("classed as positive")
     

if __name__=="__main__":            
    argparser = argparse.ArgumentParser()
    argparser.add_argument("annotated_file")
    argparser.add_argument("folder_containing_line_files")
    args = argparser.parse_args()

    fol = args.folder_containing_line_files
    if fol[-1]=="/": fol = fol[:-1]
    file_suffix = "list" #"raw.precleaned.birecoded.cleaned.noblank.melttok.truecased.2000-2016.en"
    
    tags = read_lines(fol+"/en_tag_questions_gram."+file_suffix)
    postag = read_lines(fol+"/en_tag_questions_gram_postag."+file_suffix)
    negtag = read_lines(fol+"/en_tag_questions_gram_negtag."+file_suffix)
    posanchor = read_lines(fol+"/en_tag_questions_gram_posanchor."+file_suffix)
    neganchor = read_lines(fol+"/en_tag_questions_gram_neganchor."+file_suffix)
    pospos = read_lines(fol+"/en_tag_questions_gram_postag_posanchor."+file_suffix)
    negneg = read_lines(fol+"/en_tag_questions_gram_negtag_neganchor."+file_suffix)
    negpos = read_lines(fol+"/en_tag_questions_gram_postag_neganchor."+file_suffix)
    posneg = read_lines(fol+"/en_tag_questions_gram_negtag_posanchor."+file_suffix)
    
    manual = read_annotated(args.annotated_file)
    
    evaluate(manual, tags, postag, negtag, posanchor, neganchor, pospos, \
            negneg, posneg, negpos)



