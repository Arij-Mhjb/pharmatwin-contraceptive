import json,time
from backend.ai.intent_classifier import IntentClassifier
DATA=[("Montre les profils SOPK","profiles_sopk"),("Qui présente une endométriose ?","profiles_endometriosis"),("Profils en alerte œstrogènes","profiles_estrogen_alert"),("Liste les contraceptifs","list_contraceptives"),("Quelles sources scientifiques existent ?","evidence_sources"),("Quel temps fera-t-il demain ?","unsupported")]
def main():
    c=IntentClassifier();correct=0;rows=[]
    for q,want in DATA:
        t=time.perf_counter();got=c.predict(q);ms=(time.perf_counter()-t)*1000;correct+=got["intent"]==want;rows.append({"question":q,"expected":want,"predicted":got["intent"],"confidence":got["confidence"],"latency_ms":round(ms,2)})
    print(json.dumps({"accuracy":correct/len(DATA),"samples":rows},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
