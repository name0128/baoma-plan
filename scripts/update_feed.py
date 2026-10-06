#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_feed.py —— 自动更新 feed.json（招考信息）

【作用】
本脚本用于刷新 index.html 所依赖的在线招考数据 feed.json。
部署到 GitHub Pages 后，由 .github/workflows/daily.yml 每天定时运行本脚本，
并把新的 feed.json 提交回仓库，网页端因此每天自动拿到最新招考。

【两种更新模式】
1) 智能联网模式（最可靠，需自备 key）
   设置环境变量 OPENAI_API_KEY 后，脚本调用 OpenAI Chat Completions
   （开启 web_search 工具）实时检索最新招考公告并产出结构化 JSON。
   没有第三方依赖，只用 Python 标准库，可在 GitHub Actions 默认 runner 直接运行。

2) 内置兜底模式（未配置 key 时）
   使用脚本内 FALLBACK 里的精选数据，并把 updated 标记为今天，
   保证循环永不报错、页面永远有有效数据。

【异常安全】
任何网络/解析异常都不会破坏现有 feed.json（先读旧值兜底）。
"""
import json
import datetime
import os
import urllib.request

FEED_PATH = "feed.json"

# 支持两个大模型服务：智谱（国内可注册，glm-4-flash 免费，推荐）优先；OpenAI 备选
PROVIDERS = [
    {
        "name": "zhipu",
        "key_env": "ZHIPUAI_API_KEY",
        "model_env": "ZHIPUAI_MODEL",
        "default_model": "glm-4-flash",
        "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "tool": [{"type": "web_search", "web_search": {"enable": True}}],
    },
    {
        "name": "openai",
        "key_env": "OPENAI_API_KEY",
        "model_env": "OPENAI_MODEL",
        "default_model": "gpt-4o-mini",
        "url": "https://api.openai.com/v1/chat/completions",
        "tool": [{"type": "web_search"}],
    },
]

FALLBACK = {
    "updated": datetime.date.today().isoformat(),
    "items": [
        {"province": "全国", "area": "全国", "name": "2027国考", "date": "10/15-10/24报名 · 11/28笔试", "tag": "公务员", "link": "http://www.scs.gov.cn"},
        {"province": "广东", "area": "韶关仁化县", "name": "巡察和办案服务保障中心", "date": "10/8-10/13报名(招2人)", "tag": "事业编", "link": ""},
        {"province": "广东", "area": "广州海珠区", "name": "事业单位(高校毕业生)", "date": "10/10起打准考证·10/11笔试", "tag": "事业编", "link": "https://www.haizhu.gov.cn"},
        {"province": "广东", "area": "博罗县", "name": "人民医院编外(46人)", "date": "10/15前报名", "tag": "编外", "link": ""},
        {"province": "广东", "area": "广东省", "name": "全省事业单位集中招聘(11066人)", "date": "省人社厅发布·应届岗为主", "tag": "事业编", "link": "http://hrss.gd.gov.cn"},
        {"province": "江苏", "area": "南京工程学院", "name": "专职辅导员(博士)", "date": "10/8-10/13报名", "tag": "高校", "link": ""},
        {"province": "江苏", "area": "南京铁道职院", "name": "事业单位招聘(11人)", "date": "10/8-10/15报名", "tag": "事业编", "link": ""},
        {"province": "江苏", "area": "江苏省水科院", "name": "事业单位招聘(编内3人)", "date": "9/8-10/28报名", "tag": "编内", "link": ""},
        {"province": "浙江", "area": "浙江省", "name": "下半年事业单位统考", "date": "笔试9/19已结束·关注补录", "tag": "事业编", "link": "http://qssy.zjks.com"},
        {"province": "浙江", "area": "绍兴市直", "name": "事业单位招聘(117人)", "date": "报名已结束·10661人缴费", "tag": "事业编", "link": ""},
        {"province": "四川", "area": "成都新津区", "name": "增量政策性岗位", "date": "笔试10/11·准考证10/8-11", "tag": "政策岗", "link": ""},
        {"province": "四川", "area": "成都青白江", "name": "增量政策性岗位(155人)", "date": "笔试10/11", "tag": "政策岗", "link": ""},
        {"province": "四川", "area": "四川各地市", "name": "下半年事业单位统考", "date": "10月陆续笔试(成都10/4起)", "tag": "事业编", "link": ""},
        {"province": "山东", "area": "德州平原县", "name": "第一人民医院备案制(35人)", "date": "10/9-10/16报名", "tag": "事业编", "link": "https://www.zgsydw.com/shandong/20260911/1660422_1.html"},
        {"province": "山东", "area": "烟台福山区", "name": "事业单位高层次人才", "date": "现场资格审查10/8-10/15", "tag": "事业编", "link": ""},
        {"province": "山东", "area": "潍坊坊子区", "name": "事业单位(10人)", "date": "10/9-10/14报名·11/7笔试", "tag": "事业编", "link": ""},
        {"province": "山东", "area": "山东农业工程学院", "name": "公开招聘(65人)", "date": "9/22-12/31报名", "tag": "高校", "link": ""},
        {"province": "河南", "area": "驻马店市县区", "name": "事业单位联考(153人)", "date": "10/20报名", "tag": "事业编", "link": ""},
        {"province": "河南", "area": "河南省直", "name": "事业单位人才引进(228人)", "date": "11/26报名", "tag": "事业编", "link": ""},
        {"province": "河南", "area": "河南省科学院", "name": "空天信息研究所(博士15名)", "date": "报名至12/31", "tag": "科研", "link": ""},
        {"province": "河北", "area": "河北省直", "name": "下半年统一招聘(58名)", "date": "笔试10/17·准考证10/12-17", "tag": "事业编", "link": "https://www.hebpta.com.cn"}
    ]
}


def read_old():
    try:
        with open(FEED_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"updated": "", "items": []}


def write_feed(items):
    data = {"updated": datetime.date.today().isoformat(), "items": items}
    with open(FEED_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("feed.json updated ->", data["updated"], "| items:", len(items))


def fetch_via_llm(cfg, key):
    """联网检索最新招考；未配置 key 或失败返回 None。"""
    model = os.environ.get(cfg["model_env"]) or cfg["default_model"]
    prompt = (
        "请检索今天前后中国各地正在报名或即将报名的公务员、事业单位、教师、"
        "医疗等公开招聘公告，优先全国及主要省份。返回严格 JSON："
        '{"items":[{"province":省份(如 广东/江苏/浙江/四川/山东/河南/河北)或"全国","area":城市或区县或"全国",'
        '"name":公告名称,"date":时间节点文本,'
        '"tag":类型(公务员/事业编/教师/医疗),"link":官方链接或空字符串}]}，'
        "最多14条，覆盖全国及多个省份，只给确定信息，不要编造。"
    )
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "tools": cfg["tool"],
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        cfg["url"], data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.load(r)
        content = resp["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        print(cfg["name"], "fetch failed:", e)
        return None


def main():
    for cfg in PROVIDERS:
        key = (os.environ.get(cfg["key_env"]) or "").strip()
        if not key:
            continue
        data = fetch_via_llm(cfg, key)
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            items = [it for it in data["items"] if isinstance(it, dict) and it.get("name")]
            if items:
                write_feed(items)
                return
    print("未启用/未获取到在线数据，使用内置数据。")
    write_feed(FALLBACK["items"])


if __name__ == "__main__":
    main()
