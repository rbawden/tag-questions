from evaluate_precision_gramtags import *
from sklearn.metrics import precision_recall_fscore_support
import numpy as np
import pandas as pd
import argparse, os, gzip
import re


def get_true_pred(gold, pred):
    y_true = []
    y_pred = []
    if ".gz" in gold: gf = gzip.open(gold, "rt")
    else: gf = open(gold, "r")
    if ".gz" in pred: pf = gzip.open(pred, "rt")
    else: pf = open(pred, "r")

    for g, p in zip(gf, pf):
        g, p = g.strip().lower(), p.strip().lower()
        if g=="" or p=="": break
        y_true.append(g)
        y_pred.append(p)
    if len(y_true)!=len(y_pred):
        exit("Gold and pred do not have an equal number of elements")
    classes = sorted(set(y_true).union(set(y_pred)))
    gf.close()
    pf.close()
    return y_true, y_pred, classes


def get_cross_tab(y_true, y_pred):
    print(pd.crosstab(pd.Series(y_true), pd.Series(y_pred), rownames=['True'], colnames=['Predicted'], margins=True))

    
def get_p_micro(y_true, y_pred, show=False):
    correct = 0
    for i, y in enumerate(y_true):
        if y==y_pred[i]: correct += 1
    if len(y_true)==0: return 0
    return correct/float(len(y_true))


def get_f_each_label(y_true, y_pred, classes, show=False):
    prec, recall, fscore, _ = precision_recall_fscore_support(np.array(y_true),
                                                    np.array(y_pred),
                                                    labels=classes,
                                                    average=None)
    if show:
        print("Prec, recall and fscore for each label")
        print(prec)
        print(recall)
        print(fscore)
        print("---------------------------")
    return fscore


def get_f_binary(y_true, y_pred, show=False):
    # print(y_true)
    # input()
    # print(y_pred)
    binprec, binrecall, binfscore, _ = precision_recall_fscore_support(np.array(y_true),
                                                                        np.array(y_pred),
                                                                        pos_label='true',
                                                                        average='binary')
    if show:    
        print("Binary (True):")
        print("\tP:"+str(binprec))
        print("\tR:"+str(binrecall))
        print("\tF:"+str(binfscore))
        print("---------------------------")
    return binfscore


def get_data_no_nones(y_true, y_pred):
    y_pred_no_nones = [y_pred[y] for y in range(len(y_pred)) if y_true[y] != "none"]
    y_true_no_nones = [y for y in y_true if y != "none"]

    return y_true_no_nones, y_pred_no_nones   


def get_p_r_f_nones(y_true, y_pred):
    correct = len([y for i, y in enumerate(y_true) if y_pred[i]=="none" and y=="none"])
    num_true = len([y for y in y_true if y=="none"])
    num_pred = len([y for y in y_pred if y=="none"])
    
    if num_pred==0: p=0
    else: p = correct/float(num_pred)
    if num_true==0: r=0
    else: r = correct/float(num_true)
    if p+r==0: f=0
    else: f = (2*p*r)/float(p+r)
    return p, r, f



def get_p_r_f_gramMiscNone(y_true, y_pred, show=False):
    p, r, f, _ = precision_recall_fscore_support(np.array(y_true),np.array(y_pred),
                                                 labels = ["gram", "misc", "none"],
                                                average=None)

    if show:
        print(pd.crosstab(pd.Series(y_true), pd.Series(y_pred),  margins=True))
    
    return p[0], r[0], f[0], p[1], r[1], f[1], p[2], r[2], f[2] 

# these aren't really precision, recall and f-score but they are
# marked as this for facility:
# p = # correct / # those that were predicted to be TQs
# r = # correct / # those that were TQs in gold tags
# f = harmonic mean of p and r
def get_p_r_f_without_none(y_true, y_pred, classes, show=False):

    assert(len(y_true)==len(y_pred))

    # get two ys eliminating those that are "none" in gold label
    y_true1, y_pred1 = get_data_no_nones(y_true, y_pred)
    correct, incorrect = 0, 0
    for i, y in enumerate(y_true1):
        #print("<"+y+":"+y_pred1[i]+">")
        #input()
        if y.strip().lower()==y_pred1[i].strip().lower():
            #print("<"+y+":"+y_pred1[i]+">")
            correct+=1
        else:
            incorrect += 1
            
    if len(y_true1)==0: recall = 0
    else: recall = correct/float(len(y_true1))
    os.sys.stderr.write("num correct = "+str(correct)+" out of "+str(len(y_pred1))+"\n")
    os.sys.stderr.write("num incorrect = "+str(incorrect)+" out of "+str(len(y_pred1))+"\n")

    # get two ys eliminating those that are "none" in pred label
    y_pred2, y_true2 = get_data_no_nones(y_pred, y_true)
    correct = 0
    for i, y in enumerate(y_true2):
        if y.strip().lower()==y_pred2[i].strip().lower(): correct +=1
            
    if len(y_pred2)==0: precision = 0
    else: precision = correct/float(len(y_pred2))

    if precision+recall==0: fscore = 0
    else: fscore = (2 * precision * recall) / float(precision + recall)

    os.sys.stderr.write("num correct = "+str(correct)+" out of "+str(len(y_pred2))+"\n")
        
    return precision, recall, fscore


def get_en_tags():
    return re.compile("(("+"|".join(get_en_aux())+")_(?:n.t_)?"+"("+"|".join(get_en_pros())+")(?:_not)?)", re.I)

def get_en_pros():
    return ["i", "you", "[h\']e", "thee", "ye", "yer", "she+", "we", "one", "they", "it", "i\'", "there", "someone", "anyone"]

def get_en_aux():
    return ["have", "had", "has", "might", "may", "will", "would", "could",
              "can", "must", "should", "shall", "ought", "do", "does", "did",
              "am", "are", "is", "was", "were", "had", "ai", "dare", "need"]

def get_regex_en_special_tags():
    return re.compile("^(inn+i.|ri+ght|e+h+|alright|all_right|see+|remember|you_know|or_what|ye+a+h+|aye|you_see|like|ok(ay)?|do_n-t_y..?_think|correct)$", re.I)

# is a tag question (miscellaneous)
def is_en_misc_tag(line):
    # can match this
    if re.match(en_special_tags, line):
        return True
    return False # default

# for real
def evaluate_gram_lex(y_true, y_pred):

    lex_correct_form, gram_correct_form, none_correct_form = 0, 0, 0
    lex_correct_class, gram_correct_class, none_correct_class = 0, 0, 0
    lex_total_true, gram_total_true = 0, 0
    lex_total_pred, gram_total_pred = 0, 0
    none_total_pred, none_total_true = 0, 0

    ctrue = []
    cpred = []
    
    # loop around all pred examples
    for true, pred in zip(y_true, y_pred):

        # get class for pred
        if pred == "none":
            tag = "none"
            none_total_pred += 1
        elif re.match(get_en_tags(), pred):
            tag = "gram"
            gram_total_pred += 1
        elif re.match(get_regex_en_special_tags(), pred) or pred=="lex":
            tag ="misc"
            lex_total_pred += 1
        else:
            #print(tag)
            tag = "gram"
            gram_total_pred += 1

        # get class for true
        if true == "none":
            gtag = "none"
            none_total_true += 1
        elif re.match(get_en_tags(), true):
            gtag = "gram"
            gram_total_true += 1
        elif re.match(get_regex_en_special_tags(), true) or true=="lex":
            gtag = "misc"
            lex_total_true += 1
        else:
            gtag = "gram"
            gram_total_true += 1

        ctrue.append(gtag)
        cpred.append(tag)

            
        # calculate how many many classes are correct    
        if tag == gtag:
            if tag == "gram": gram_correct_class += 1
            elif tag == "misc": lex_correct_class += 1
            elif tag =="none": none_correct_class += 1

        # calculate individual precision
        if pred == true:
            if tag == "gram": gram_correct_form += 1
            elif tag == "misc": lex_correct_form += 1
            elif tag =="none": none_correct_form += 1        

    # matrix
    #print("showing class crosstab")
    #print(get_cross_tab(ctrue, cpred))

    #print("gram:")
    #for thing in ["gram", "misc", "none"]:
    #    print("\t"+str(len([c for c, t in zip(ctrue, cpred) if c=="gram" and t==thing])))
    #print("misc")
    #for thing in ["gram", "misc", "none"]:
    #    print("\t"+str(len([c for c, t in zip(ctrue, cpred) if c=="misc" and t==thing])))
    #print("none")
    #for thing in ["gram", "misc", "none"]:
    #    print("\t"+str(len([c for c, t in zip(ctrue, cpred) if c=="none" and t==thing])))

          
    results = []
    correct_class = [gram_correct_class, lex_correct_class, none_correct_class]
    correct_form = [gram_correct_form, lex_correct_form, none_correct_form]
    totpreds = [gram_total_pred, lex_total_pred, none_total_pred]
    tottrues = [gram_total_true, lex_total_true, none_total_true]
    
    for correctc, correctf, totpred, tottrue in zip(correct_class, correct_form, totpreds, tottrues):
        if totpred==0: p=0
        else: p = correctc/totpred
        if tottrue==0: r=0
        else:r = correctc/tottrue
        if p+r==0: f=0
        else: f = (2*p*r)/float(p+r)
        if totpred==0:
            pform=0
        else: pform = correctf/totpred
            
        results.append((p, r, f, pform))

    return(results)
                
    

    os.sys.stderr.write("Accuracy on pred gram = "+str(gram_correct_class/float(gram_total_pred))+"\n")
    os.sys.stderr.write("Accuracy on pred lex = "+str(lex_correct_class/float(lex_total_pred))+"\n")
    os.sys.stderr.write("Accuracy on pred none = "+str(none_correct_class/float(none_total_pred))+"\n")
    # os.sys.stderr.write("Accuracy on pred TQ = "+str((gram_correct+lex_correct)/float(gram_total_pred+lex_total_pred))+"\n")

    os.sys.stderr.write("\nAccuracy on true gram = "+str(gram_correct_class/float(gram_total_true))+"\n")
    os.sys.stderr.write("Accuracy on true lex = "+str(lex_correct_class/float(lex_total_true))+"\n")
    os.sys.stderr.write("Accuracy on true none = "+str(none_correct_class/float(none_total_true))+"\n")
    # os.sys.stderr.write("Accuracy on true TQ = "+str((gram_correct+lex_correct)/float(gram_total_true+lex_total_true))+"\n")

    print("\nLEX")
    print(lex_total_pred)
    print(lex_total_true)
    print("\nGRAM")
    print(gram_total_pred)
    print(gram_total_true)
    print("\nNONE")
    print(none_total_pred)
    print(none_total_true)
    # print("\nTOTAL")
    # print(none_total_pred+gram_total_pred+lex_total_pred)
    # print(none_total_true+gram_total_true+lex_total_true)
    return results
    
def merge_classes(y_true, y_pred):
    for y_list in [y_true, y_pred]:
        for y in range(0,len(y_list)):
            if y_list[y]=="okay": y_list[y]="ok"
    return y_true, y_pred


def article_eval(y_true, y_pred):
    gram, lex, none = evaluate_gram_lex(y_true, y_pred)
    totalprecision = get_p_micro(y_true, y_pred)

    # precision for gram and lex
    row = ""
    for x in gram, lex, none:
        row += " & " + " & ".join([str(round(y*100,2)) for y in x])
    row += " & " + str(round(totalprecision*100,2)) + " \\\ "

    print(row)
    


def normalise_classes(y_true, y_pred):
    # change pred if there is a certain form (compared to true)
    for i, (true, pred) in enumerate(zip(y_true, y_pred)):
        if true.replace("ai_n-t", "is_n-t")==pred: y_pred[i] = true
        elif true.replace("ai_n-t", "are_n't")==pred: y_pred[i] = true
        elif true.replace("ai_n-t", "has_n-t")==pred: y_pred[i] = true
        elif true.replace("ai_n-t", "have_n-t")==pred: y_pred[i] = true
        elif pred=="does_n-t_it" and true=="do_n-t_it": y_pred[i] = true
        elif pred+"_not" == true.replace("_", "_n-t_").replace("_n-t_not", "_not"): y_pred[i] = true
    return y_true, y_pred


if __name__=="__main__":

    argparser = argparse.ArgumentParser()
    argparser.add_argument("gold")
    argparser.add_argument("pred")
    argparser.add_argument("-binary", action='store_true', default=False)
    argparser.add_argument("-noshow", action='store_true', default=False)
    argparser.add_argument("-t", choices=["tagnottag", "fine", "finer", "real", "gramMiscNone", "gramMiscTypeNone", "article"], required=True)
    args = argparser.parse_args()

    y_true, y_pred, classes = get_true_pred(args.gold, args.pred)
    y_true, y_pred = normalise_classes(y_true, y_pred)

    # numok_true = len([x for x in y_true if x=="ok"])
    # numok_pred = len([x for x in y_pred if x=="ok"])
    # os.sys.stderr.write(str(numok_true)+"\n")
    # os.sys.stderr.write(str(numok_pred)+"\n")


    if args.t == "article":
        article_eval(y_true, y_pred)
    elif args.binary:
        fscore = get_f_binary(y_true, y_pred, not args.noshow)
        os.sys.stdout.write(str(fscore))

    elif args.t=="gramMiscNone":
        allresults = get_p_r_f_gramMiscNone(y_true, y_pred, show=not args.noshow)
        os.sys.stdout.write("\t".join([str(res) for res in allresults])+"\n")

        evaluate_gram_lex(y_true, y_pred)
        
    else:
        p_micro = get_p_micro(y_true, y_pred, not args.noshow) #overall labelling precision
        p_tq, r_tq, f_tq = get_p_r_f_without_none(y_true, y_pred, classes, not args.noshow)
        f_each = get_f_each_label(y_true, y_pred, classes, not args.noshow)
        pnone, rnone, fnone = get_p_r_f_nones(y_true, y_pred)

        os.sys.stdout.write(" ".join([str(x) for x in [p_tq, r_tq, f_tq, pnone, rnone, fnone, p_micro]]))

        evaluate_gram_lex(y_true, y_pred)
        

