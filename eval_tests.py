import re
import subprocess
import os
import sys
import numpy as np
import math
import itertools
#import nltk
#from sklearn.metrics import cohen_kappa_score
#from nltk import agreement

filepath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, filepath)

#Dictionaries mapping the responses to numerical values
yn_to_index = {"yes": 4, "rather yes": 3, "uncertain": 2, "rather no": 1, "no": 0}
rel_to_index = {"right": 0, "left": 1, "in front of": 2, "behind": 3, "above": 4, "below": 5, "over": 6, "under": 7, "in": 8, "on": 9, "at": 10, "touching": 11, "between": 12, "near": 13}

rel_accuracy = {"right": [0,0], "left": [0,0], "front": [0,0], "behind": [0,0], "above": [0,0], "over": [0,0], "below": [0,0], "under": [0,0], "between": [0,0], "at ": [0,0], "touching": [0,0], "near": [0,0], "in ": [0,0], "on ": [0, 0]}

#Maps the response to its numerical value
def map_response_to_index(resp):
    for key in rel_to_index:
        if key in resp:
            return rel_to_index[key]
    return -1

#Computes the weighted Cohen's Kappa interannotator agreement metric
#Inputs: resp1, resp2 - response sequences for two users
#Return value: the Kappa coefficient (from [0, 1])
def weighted_cohen_kappa(resp1, resp2, use_weighted=False):
    weights = np.zeros((5,5))
    for i in range(weights.shape[0]):
        for j in range(weights.shape[1]):            
            weights[i][j] = abs(i - j) if use_weighted else int(i != j)

    if len(resp1) > 0 and len(resp2) > 0:
        resp_distr = np.zeros((5, 5))
        for i in range(len(resp1)):
            resp_distr[resp1[i]][resp2[i]] += 1
        total_resp = np.sum(resp_distr)
        observed_agreement = sum([resp_distr[i][i] for i in range(resp_distr.shape[0])]) * 1.0
        observed_agreement /= total_resp
        total_coincidence = 1.0 * sum([np.sum(resp_distr[i,:]) * np.sum(resp_distr[:,i]) for i in range(resp_distr.shape[0])])
        total_coincidence /= total_resp * total_resp
        kappa = (observed_agreement - total_coincidence) / (1 - total_coincidence)
        num = 0
        denom = 0
        for i in range(5):
            for j in range(5):
                num += weights[i][j] * resp_distr[i][j]
                denom += weights[i][j] * np.sum(resp_distr[i,:]) * np.sum(resp_distr[:,j])
        weighted_kappa = 1 - total_resp * 1.0 * num / denom
        #print (resp_distr, total_resp, total_coincidence, observed_agreement, "Kappa:", kappa, "weighted kappa:", weighted_kappa)
        #print ("KAPPA METRIC: {}; WEIGHTED_KAPPA: {}".format(kappa, weighted_kappa))
        return weighted_kappa
    return 0

#Computes the standard Cohen's Kappa interannotator agreement metric
#Inputs: resp1, resp2 - response sequences for two users
#Return value: the Kappa coefficient (from [0, 1])
def cohen_kappa(resp1, resp2):
    y1 = []
    y2 = []
    for testcase in resp1:
        if testcase in resp2:
            y1 += [resp1[testcase]]
            y2 += [resp2[testcase]]
    y1 = [rel_to_index[y] for y in y1]
    y2 = [rel_to_index[y] for y in y2]

    if len(y1) > 0 and len(y2) > 0:
        resp_distr = np.zeros((13, 13))
        for i in range(len(y1)):
            resp_distr[y1[i]][y2[i]] += 1
        total_resp = np.sum(resp_distr)
        observed_agreement = sum([resp_distr[i][i] for i in range(resp_distr.shape[0])]) * 1.0
        observed_agreement /= total_resp
        total_coincidence = 1.0 * sum([np.sum(resp_distr[i:]) * np.sum(resp_distr[:i]) for i in range(resp_distr.shape[0])])
        total_coincidence /= total_resp * total_resp
        kappa = (observed_agreement - total_coincidence) / (1 - total_coincidence)
        #print (resp_distr, total_resp, total_coincidence, observed_agreement, kappa)        

tests = []
count = 0
trc = 0
desc = 0
tcounts = {}
ur_yn = {}
ur_relations = {}
relatums = {}
system_yn = {}
test_counter = 0
tj_count = 0
descr_count = 0
descr_success = 0
suggested_rels = {}
tjs_by_testcase = {}
by_relation = {}

annotations = [annotation.strip().split(":") for annotation in open('annotations').readlines()]
ur_yn["system"] = {}
#def process_annotation(annotation):
    
#Main annotation evaluation pipeline
for subm in annotations:

    #Read-off the annotation components
    #subm = subm.strip().split(":")
    ID = subm[0].split("=")[1]
    testcase = subm[1].split("=")[1]
    user = subm[2].split("=")[1]
    scene_path = subm[4].split("=")[1]
    relation = subm[5].split("=")[1]
    relatum = subm[6].split("=")[1]
    referent1 = subm[7].split("=")[1]
    referent2 = subm[8].split("=")[1]
    task_type = subm[9].split("=")[1]
    resp = subm[10].split("=")[1].lower()
    scene_path = scene_path.replace("/", os.sep)
    if user not in ur_yn:
        ur_yn[user] = {}
    if user not in ur_relations:
        ur_relations[user] = {}    
    if task_type == "1" and int(ID) > 1002396:
        print ("ID:", ID, resp, user, testcase, task_type)

        #Call Blender with the extracted annotation data
        result = subprocess.check_output(["blender", scene_path, "--background", "--python", "main.py", "--", relation, relatum, referent1, referent2, task_type, resp])
        result = result.decode("utf-8").split("\n")

        #Print the evaluation results
        res = ""
        for item in result:
            if "RESULT" in item:
                res = (item.split(":")[1]).strip()
                break

        rel = ""
        for key in rel_accuracy:
            if key in resp and (key != "in " or "front" not in resp):
                rel = key
                break
        rel_accuracy[rel][0] += 1
        descr_count += 1
        if res == "1" or res == "0":
            res = int(res)
            descr_success += res
            rel_accuracy[rel][1] += res
        if res != 1:
            print ("{}\nRESULT: {}".format(result, res))

        '''if testcase not in suggested_rels:
            ur_relations[testcase] = {}
            for rel in relations:
                if rel in resp and (rel != "in" or rel == "in" and "in " in resp and "front" not in resp):
                    ur_relations[testcase][user] = rel

            result = subprocess.check_output(["blender", scene_path, "--background", "--python", "main.py", "--", " ", relatum, " ", " ", "2", " "])
            result = result.decode("utf-8").split("\n")
            res = ""
            for item in result:
                if "RESULT" in item:
                    res = (item.split(":")[1]).strip()
                    break
            suggested_rels[testcase] = res.split("#")
            print (res.split("#"))'''
        
    elif task_type == "0" and int(ID) > 1002396:# and ("above" == relation or "below" == relation):
        result = []
        if tj_count < 2000:
            result = subprocess.check_output(["blender", scene_path, "--background", "--python", "main.py", "--", relation, relatum, referent1, referent2, task_type, resp])
            result = result.decode("utf-8").split("\n")
        print (result)
        if testcase not in tjs_by_testcase:
            tjs_by_testcase[testcase] = {}
        tjs_by_testcase[testcase][user] = yn_to_index[resp]
        ur_yn[user][testcase] = yn_to_index[resp]
        tj_count = tj_count + 1
        res = ""
        for item in result:
            if "RESULT" in item:
                res = (item.split(":")[1]).strip()
                break
        if res is not None and res != "":
            res = math.floor(5 * float(res))
            system_yn[testcase] = res
            ur_yn["system"][testcase] = res
            if relation not in by_relation:
                by_relation[relation] = (0, 0)
            by_relation[relation] = (by_relation[relation][0] + 1, by_relation[relation][1] + int(res == yn_to_index[resp]))            
        print ("RESULT:", res, "USER RESULT:", ur_yn[user][testcase])
    print ("TOTAL PROCESSED: {}".format(descr_count + tj_count))


if descr_count != 0:
    print ("DESCRIPTION TASK ACCURACY: {}".format(descr_success / descr_count))
    print ("PER-RELATION ACCURACY: {}".format([(key, rel_accuracy[key], float(rel_accuracy[key][1]) / rel_accuracy[key][0]) for key in rel_accuracy if rel_accuracy[key][0] != 0]))
    
    correct_suggestions = 0
    for key in suggested_rels:
        for user in ur_relations[key]:
            if ur_relations[key][user] in suggested_rels[key]:
                correct_suggestions += 1
                break

    print ("SUGGESTION ACCURACY: {}".format(correct_suggestions / descr_count))

#Compute and print the interannotator agreement
if tj_count != 0:
    avg_hh_weighted = 0.0
    avg_hs_weighted = 0.0
    total_hh = 0
    total_hs = 0
    avg_hh_kappa = 0.0
    avg_hs_kappa = 0.0
    for keys in itertools.combinations(ur_yn.keys(), r = 2):
        #for testcase in tjs_by_testcase:    
        #test1 = sorted([id for id in ur_yn[keys[0]]])
        #test2 = sorted([id for id in ur_yn[keys[1]]])
        #shared_testcases = sorted([testcase for testcase in tjs_by_testcase \
        #if (keys[0] in tjs_by_testcase[testcase] and keys[1] in tjs_by_testcase[testcase])])
        intersect = [testcase for testcase in ur_yn[keys[0]] if testcase in ur_yn[keys[1]]]
        if intersect != []:
            print (keys)
            resp1 = [ur_yn[keys[0]][testcase] for testcase in intersect]
            resp2 = [ur_yn[keys[1]][testcase] for testcase in intersect]
            weighted_kappa = weighted_cohen_kappa(resp1, resp2, True)
            kappa = weighted_cohen_kappa(resp1, resp2, False)
            #print ("SKLEARN KAPPA: {}".format(cohen_kappa_score(resp1, resp2)))
            #taskdata = [[0, str(i), str(resp1[i])] for i in range(len(resp1))] + [[1, str(i), str(resp2[i])] for i in range(len(resp2))]
            #task = agreement.AnnotationTask(data = taskdata)
            #print ("NLTK KAPPA: {}".format(str(task.kappa())))
            if "system" in keys:
                avg_hs_weighted += weighted_kappa
                avg_hs_kappa += kappa
                total_hs += 1
            else:
                avg_hh_weighted += weighted_kappa
                avg_hh_kappa += kappa
                total_hh += 1

    print ("AVG WEIGHTED KAPPA. HUMAN-HUMAN: {}; HUMAN-SYSTEM: {}".format(avg_hh_weighted / total_hh, avg_hs_weighted / total_hs))
    print ("AVG KAPPA. HUMAN-HUMAN: {}; HUMAN-SYSTEM: {}".format(avg_hh_kappa / total_hh, avg_hs_kappa / total_hs))
    print (by_relation)
