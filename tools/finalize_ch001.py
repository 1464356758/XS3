#!/usr/bin/env python3
"""Complete author-reviewed CH001 with V4.3 immutable adopt protocol.

This does not generate prose or assume reviewer independence. It consumes:
- eight manually authored and inspected narrative segments;
- explicitly authored scene, dialogue, resource and causality review evidence.
Release-check must accept each citation; no bypasses to validation.
"""
from __future__ import annotations
from pathlib import Path
import json
import sys
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "tools"))
import novel_state as ns
import online_state as osys

ROOT = PROJECT / "book"
DRAFTS = PROJECT / "drafts"
EDITORIAL = json.loads((DRAFTS / "CH001_editorial_review.json").read_text("utf-8"))

def store(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    ns.atomic_json(path, value)

def evidence(text_sha, quote):
    if not isinstance(quote, str) or not quote or quote not in manuscript:
        raise RuntimeError(f"人工审核证据未对应正文: {quote!r}")
    return {"chapter": 1, "sha256": text_sha, "quote": quote}

def checked_state():
    s = ns.load_state(ROOT)
    ns.verify_files(ROOT, s)
    assert s["book_id"] == "7be49326-b891-4d4a-ad8c-7f189ed00645", "Book identity mismatch"
    assert s["title"] == "《大旱三年，我替县城算活路》", "Title mismatch"
    assert s["revision"] == 3 and not s["chapters"] and not s["tasks"], "Concurrent chapter task or changed formal revision"
    assert s["config"]["serial_mode"] is True
    assert s["config"]["narrative_review_required"] is True
    assert not s["serialization"]["frozen"] and not s["serialization"]["published"]
    assert s["inputs"]["canon"]["sha256"] == "5728c47dc6d664664b63fc8e0877d9ca26972091a7bba8622087fdbcb44807ad"
    assert s["inputs"]["roadmap"]["sha256"] == "6bb43c212424d014e289097086d1fe10a1520441e694f1691229ab86c781876b"
    w = osys.load_workflow(PROJECT)
    assert w["phase"] == "PLANNING" and w["selected_topic"]["id"] == "T01"
    return s

state = checked_state()
parts = [(DRAFTS / "CH001_parts" / f"{i:02d}.txt").read_text("utf-8").strip()
         for i in range(1, 9)]
manuscript = "\n\n".join(parts) + "\n"
assert manuscript.startswith("仓门外第三根拒马被撞倒时"), "Unexpected opening"
manuscript = manuscript.replace("仓门外第三根拒马被撞倒时",
                                "景宁十六年五月初九，仓门外第三根拒马被撞倒时", 1)
assert manuscript.count("每日九两粗粮配额") == 1, "Unit correction target absent/duplicated"
manuscript = manuscript.replace("每日九两粗粮配额", "每人每日十分之九斤粗粮配额")
assert "九两粗粮" not in manuscript
count = ns.han_count(manuscript)
assert 8000 <= count <= 10000, f"Formal Chinese character count out of range: {count}"
assert len(parts) == 8 and all(ns.han_count(x) > 900 for x in parts)
assert not ns.narrative_module().surface_scan(manuscript), "Unexpected production text"
text_sha = ns.digest(manuscript)
text_path = DRAFTS / "CH001.txt"
ns.atomic_text(text_path, manuscript)
print("CH001 draft:", count, "Han", text_sha)

# The writing brief is completed from the already-read canon, roadmap and actual
# authored segments. Stage budget is a planning aid, not a proxy for actual count.
brief_path = DRAFTS / "CH001_writing_brief.json"
ns.narrative_module().request_brief(ROOT, brief_path, ns.serial_api())
brief = ns.read_json(brief_path)
brief.update({
  "decision":"ready",
  "writer_brief":"写景宁十六年五月初九的北阜县仓门危机：许砚被扣三百袋失粮责任，先封原账、守住证人，促成不同人双重盘袋。他承认自家抄簿漏洞但不能接受用未知去向定盗粮罪。县令有权县内核验而无权跨县挪粮；粮必须仍不足三日。用母亲和门外一只空碗体现行动代价，尾声发现外衙验转副联被改押的可查线索。不得提前认定主谋或发放整仓。",
  "hard_boundaries":[
    "本书无系统或现代技术外挂，所有纸证、证人及官职权限均需合理。",
    "账面460袋、实盘160袋、缺300袋共15000斤；现存160袋名额8000斤，不可冒充净重；每袋名额50斤。",
    "已登记待赈3000人每人每日十分之九斤，预计每天2700斤；理论2.96天尚未扣耗。另仓种粮72袋3600斤绝不合并当日可发。",
    "杜延衡只准本县临时核验和依法候发，不能越县调粮；廖十二不随意放人；石景楼有仓丞的签字和钥匙但不等于知晓全部去向。",
    "清晨至申时不跳日，许砚只知验转押痕、不提前知道最终粮去向；母亲夜车见闻只记未核。",
    "今日不得伪造已发粮、已公开定罪或已结案；原账封存，许砚仍有镣铐。",
    "第一章800字内出现问罪与粮差，3000字内主角已主动改变证物保护程序；结尾以可查实物副联而非抽象神秘收尾。"
  ],
  "reader_promise":"高压现场与人命倒计时并行。一个穷账房必须付出自身认错的代价才可争取查证机会，敌对角色各有权限与现实利益；章末既有有限胜利也有尚饿的人群。",
  "history_queries":[],
  "scene_plan":[
    {"purpose":"仓门受押，立刻报出差额与三日极限，主角请求守证与独立复数", "target_han":1100},
    {"purpose":"独立点袋、封锁钥匙和账页孔迹；显出旧账不可轻断罪", "target_han":1200},
    {"purpose":"呈报与当发告示让核证和救人时间产生真正冲突", "target_han":1150},
    {"purpose":"母亲夜车未核见闻和欠药价，把人际代价压到主角身上", "target_han":1100},
    {"purpose":"县令审问，县权合法授权，正式处理种粮不能随意拆封", "target_han":1250},
    {"purpose":"门外群众旧队号和未登记者暂册，留一笔真实伤害与责任", "target_han":1150},
    {"purpose":"逐账核额，主角承认二十四袋补登疏漏，证人供述层级分离", "target_han":1150},
    {"purpose":"封查收束，发现验转副联旧押与州字残痕，权力与粮源问题打开", "target_han":1350},
  ]
})
assert sum(x["target_han"] for x in brief["scene_plan"]) == 9450
store(brief_path, brief)
ns.narrative_module().check_brief(ROOT, brief_path, ns.serial_api())
_ = ns.narrative_module().writer_packet(ROOT, ns.load_state(ROOT), ns.serial_api())
print("Writing brief checked")

# One-time full draft candidate registration. The text is complete; no fake repairs.
ns.candidate(ROOT, 1, text_path, "write", "真实完成的CH001八场完整初稿；正式计数已确认")
print("Candidate registered")

record = {
  "chapter":1, "title":"八千斤粮", "stage":"S01",
  "base_revision":ns.load_state(ROOT)["revision"],
  "canon_sha256":state["inputs"]["canon"]["sha256"],
  "text_sha256":text_sha, "complete":True,
  "story_time_end": 660,
  "summary":"五月初九晨，北阜官仓账面460袋，双人点袋160袋，差300袋但未证明被盗。许砚带镣铐争取封存原账、异人点袋和县令限当日临时核验，承认昨夜抄簿时对24袋补登入仓凭证的疏漏。杜延衡承认今日误时，保留原领牌次序并要求未登记者另立暂册。许母说昨夜听到三辆车，未见载货或车上人物，此信息登记未核。尾声一张出运副联被发现外衙验转押改盖，下有疑似州字，尚无法查明失粮去向。县民仍未领到粮，许砚仍受监。",
  "review":{
    "read_full_text":True,"decision":"adopt","blocking_issues":[],
    "sources_checked":[],
    "conclusion":"已逐场审核同日时序、账额、票据可信度、官职权力、证人限知与人物自主选择。旧版草稿配给写法存在两制歧义，正式正文统一为每人每日十分之九斤；检查文内数字、各场因果和章尾未完成承诺，无剩余必须修项。同上下文审读不是独立真实读者。"
  },
  "facts":[
    {"kind":"fact","key":"time:CH001:date","value":"景宁十六年五月初九，清晨至申时进行封仓核查。","holder":"","valid_from":0,"valid_until":None,"quote":"景宁十六年五月初九，仓门外第三根拒马被撞倒时"},
    {"kind":"state","key":"warehouse:northfu:bags-counted","value":"两名独立点袋人各得160袋；袋数确定，实重未逐袋验。","holder":"","valid_from":140,"valid_until":None,"quote":"第一人报一百六十，第二人也报一百六十。"},
    {"kind":"state","key":"warehouse:northfu:book-shortfall","value":"账面应存460袋，实盘160袋，袋数差300袋，不能直接等同被偷。","holder":"","valid_from":0,"valid_until":None,"quote":"少的三百袋，谁签的数？"},
    {"kind":"state","key":"resources:northfu:seed-reserve","value":"县令明确另仓种粮72袋、3600斤封存，不纳入现可赈粮。","holder":"","valid_from":400,"valid_until":None,"quote":"种粮三千六百斤，另仓封存，不入眼前八千斤。"},
    {"kind":"state","key":"resources:northfu:food-grain-nominal","value":"160袋每袋名额50斤，名额总量8000斤，逐袋实重未验。","holder":"","valid_from":430,"valid_until":None,"quote":"名额八千斤，净重待验"},
    {"kind":"state","key":"legal:xuyan:status","value":"许砚仍被拘押并获受监旁证核验机会，没有获无罪或正式释放。","holder":"","valid_from":580,"valid_until":None,"quote":"你要的本官给了，但给你的不是清白。"},
    {"kind":"state","key":"legal:northfu:temporary-order","value":"杜县令签仅限当日仓内核数、封账、留证之令；未授权跨县调粮。","holder":"","valid_from":570,"valid_until":None,"quote":"这个令只准你们今日核数、封账、留证。"},
    {"kind":"state","key":"relief:unregistered:ledger","value":"未登记赈户暂册由县衙建立；不等于已经取得正式配给资格。","holder":"","valid_from":500,"valid_until":None,"quote":"无号者另立暂册。"},
    {"kind":"knowledge","key":"witness:mother:night-carts","value":"母亲听见三辆车，未认出人，未见车内粮；证词待核。","holder":"许母","valid_from":220,"valid_until":None,"quote":"我眼睛不好，认不清人。"},
    {"kind":"knowledge","key":"document:xuyan:altered-endorsement","value":"看到外衙验转副联旧押被盖改与下层州字残痕，但不知粮真实去向。","holder":"许砚","valid_from":650,"valid_until":None,"quote":"是一个“州”字的下半截。"},
    {"kind":"belief","key":"warehouse:shijinglou:account","value":"石景楼声称晨间仅因账页线损而重装账册，尚未核实。","holder":"石景楼","valid_from":430,"valid_until":None,"quote":"旧线断了，今晨重新穿的。"},
    {"kind":"state","key":"family:xuyan:medicine-debt","value":"许家药铺仍欠九十文，为母亲取药有现实缺口。","holder":"","valid_from":220,"valid_until":None,"quote":"欠了九十文。"}
  ],
  "progression":{
    "goal":"许砚保命并厘清官仓差额，在兑粮危机中阻止原证毁损。",
    "obstacle":"身为嫌犯无权开仓调粮，三千赈户等不到当日米，县令担心城乱与问责，仓丞可控制账钥。",
    "method":"申请捕头封钥、两名无关人员重数、实物与账目分开核，限制证人声称的事实等级，并推动有权者签临时核验令。",
    "choice":"许砚承认自己未查24袋补登入仓凭据的职业疏漏，同时要求该责任与300袋真实去向分开。",
    "result":"两名独立点袋160袋，县令签当日核验令、保留原领牌与另立暂册，尾声证物出现外衙改押线索。",
    "consequence":"许砚仍遭拘问，药债和门外饥饿未解；限今日核验并留下实名责任，杜县令与捕头须承担延迟赈粮风险。",
    "next_options":"CH002逐户复核原领牌与城外暂册，核外衙存根的实际保存与调取权限；不得假定失粮已追回。",
    "scene_function":"八场分别完成危机引爆、独立盘袋、时间代价、亲情与未知证词、县权决策、排号矛盾、抄账责任和实物线索，非同一种嘴战循环。"
  },
  "thread_events":[
    {"action":"plant","id":p["id"],"description":p["description"],"quote":p["quote"]}
    for p in EDITORIAL["promises"]
  ],
  "stage_closing":False
}
record_path=DRAFTS/"CH001_record.json"
store(record_path,record)
ns.validate_record(ROOT,ns.load_state(ROOT),manuscript,record)
print("Record validated")
# Only current chapter included, no prior frozen prose. Do not assert independent reader.
reader_packet, coverage = ns.narrative_module().reader_packet(ROOT, ns.load_state(ROOT), manuscript, ns.serial_api())
assert coverage["1"]["mode"]=="full_text" and ns.digest(manuscript) == coverage["1"]["text_sha256"]
request_path=DRAFTS/"CH001_release_review.json"
ns.serial_module().request(ROOT,text_path,record_path,request_path,ns.serial_api())
report=ns.read_json(request_path)
report.update({
  "decision":"release","read_full_text":True,"blocking_issues":[],
  "reader_reason_to_continue":"改押副联与州字残痕构成能按真实权限调查的悬念，三千人等不到粮的下一步也明确。",
  "consequence":"受监核验以名义计数与正式文书保住证物，同时使许砚明确承担昨夜二十四袋补登漏查的责任；空碗和未登记暂册尚未救活任何人。",
  "ending_runway":"下一章由仓门长谈切换到排号和街坊实际人头，再推进可发粮净重与外衙证据的可行调取，既不提前找到真相也不复制本章核证。"
})
for key, item in EDITORIAL["checks"].items():
    assert key in report["checks"], key
    report["checks"][key] = {"decision":"pass","conclusion":item["conclusion"],"evidence":[evidence(text_sha,item["quote"])]}
assert not report["comparison"], "Unexpected prior chapters"
for item in report["future_window"]:
    f=next(x for x in EDITORIAL["future"] if x["chapter"]==item["chapter"])
    item.update(goal=f["goal"],change=f["change"],ending_question=f["ending_question"])
for item in report["promise_reviews"]:
    entry=next(x for x in EDITORIAL["promises"] if x["id"]==item["id"])
    item.update(action="set",deadline_chapter=entry["deadline_chapter"],reason=f"首章建立待兑现承诺：{entry['description']}。按选题规划的未采用后续章节设定期限，不把疑问写成已经完成。",evidence=evidence(text_sha,entry["quote"]))
assert len(report["promise_reviews"])==4 and not report["incident_actions"]
report["opening"]=EDITORIAL["opening"]
for field in ("first_hook","core_promise","protagonist_impact"):
    assert report["opening"][field]["quote"] in manuscript
nr=report["narrative_review"]
nr["actual_scenes"]=[
 {"event":s["event"],"choice":s["choice"],"change":s["change"],"evidence":[evidence(text_sha,s["quote"])]}
 for s in EDITORIAL["observed_scenes"]
]
nr["plan_comparison"]="八场写作计划全部有实际正文证据；与初定纲要相较，增加了无号者暂册、母亲证词限知、二十四袋补登漏审和净重待验四处独立代价，未提前证实三百袋的去向，也未启动大规模发粮。"
nr["reader"].update({
    "mode": "same_context_approximation",
    "limitation": EDITORIAL["reader"]["limitation"],
    "understanding": EDITORIAL["reader"]["understanding"],
    "information_load": EDITORIAL["reader"]["information_load"],
    "promise_delivery": EDITORIAL["reader"]["promise_delivery"],
    "evidence":[evidence(text_sha,EDITORIAL["reader"]["quote"])],
    "issues":[{"severity":i["severity"],"status":i["status"],"reason":i["reason"],"evidence":evidence(text_sha,i["quote"])} for i in EDITORIAL["reader"]["issues"]]
})
for k, item in EDITORIAL["character_causality"].items():
    nr["character_causality"][k]={"status":"reviewed","conclusion":item["conclusion"],"evidence":[evidence(text_sha,item["quote"])]}
nr["history"].update({"queries":[],"comparisons":[],"no_match_reason":"首章。正式仓库尚无已采用章节，历史索引是零条；不能声称与不存在的前章做过全文反重复比较。已按本章八场实际办法、选择和后果检查内部重复。"})
nr["reader_updates"]=[
 {"kind":u["kind"],"statement":u["statement"],"evidence":[evidence(text_sha,u["quote"])]}
 for u in EDITORIAL["reader_updates"]
]
nr["reader_update_note"]="有实证的点袋数、县令局部授权，与仓丞自述和外衙旧印疑点分别记录，不把人物说法升格为客观事实；不把未发粮写成已发。"
assert not nr["surface_findings"]
store(request_path,report)
ns.serial_module().check(ROOT,text_path,record_path,request_path,ns.serial_api())
print("Release-check: passed")
result=ns.adopt(ROOT,text_path,record_path)
print("Adopt:",json.dumps(result,ensure_ascii=False))
assert result["chapter"]==1 and result["han_count"]==count
final=ns.load_state(ROOT)
ns.verify_files(ROOT,final)
assert "1" in final["serialization"]["frozen"]
assert final["serialization"]["published"]=={}
assert "2" not in final["chapters"]
assert len(final["chapters"]) == 1
assert final["tasks"]["1"]["phase"]=="adopted"
assert final["inputs"]==state["inputs"]
# Author has authorized writing + adoption only, NOT platform publication.
osys.set_task(PROJECT,"PLANNING","CH001《八千斤粮》已完成实测汉字、审读、发布前检查并定稿冻结；暂无平台发布回执。下一章须读取本章全部冻结正文。","开始CH002《门外三千人》前先核对木牌旧序、暂册、库存净重与外衙验转副联；仅写下一章。",chapter=2)
osys.build_index(PROJECT)
check=osys.validate_index(PROJECT)
assert check["valid"] is True and check["chapters"]==1
print("Index validated:",json.dumps(check,ensure_ascii=False))
print("FORMAL_TEXT_PATH=book/"+final["chapters"]["1"]["text_path"])
print("FORMAL_RECORD_PATH=book/"+final["chapters"]["1"]["record_path"])
print("FORMAL_RELEASE_PATH=book/"+final["serialization"]["gates"]["1"]["path"])
print("FORMAL_SHA256="+final["chapters"]["1"]["text_sha256"])
print("FORMAL_HAN="+str(final["chapters"]["1"]["han_count"]))
print("PUBLISHED_CHAPTERS="+str(len(final["serialization"]["published"])))
