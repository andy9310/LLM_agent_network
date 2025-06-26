#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
output of algorithm : ("流量往哪放", "開關")
Library: 把 ['L1','L3','L6'] 轉成
  (a) 對應的 curl 指令清單
  (b) 對應的 config JSON 物件
  (c) 亦可直接把 config_<iface>.json 寫到磁碟
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

json_path = Path("topology.json")
with json_path.open(encoding="utf-8") as f:   # 建議加上 encoding
    data = json.load(f)

LINK_TO_IF: Dict[str, str] = 
REST_ROOT_FMT = ("http://{host}:{port}/restconf/operational/"
                 "network-topology:network-topology/topology/topology-netconf/"
                 "node/{node}/yang-ext:mount/Cisco-IOS-XR-ifmgr-cfg/"
                 "interfaces/interface/{iface}")

def _iface_to_url(iface: str, *, host: str, port: int, node: str) -> str:
    safe = iface.replace("/", "%2F")
    return REST_ROOT_FMT.format(host=host, port=port, node=node, iface=safe)

def build_commands(links: List[str], *, host="localhost", port=8181,
                   node="node9", auth="admin:admin") -> List[str]:
    """回傳每條 link 的 curl 指令。"""
    cmds = []
    for l in links:
        iface = LINK_TO_IF[l]
        url = _iface_to_url(iface, host=host, port=port, node=node)
        cmd = (f"curl -u {auth} -X PATCH "
               f"-H 'Content-Type: application/yang-data+json' \\\n"
               f"     {url} -d @config_{iface.replace('/', '_')}.json")
        cmds.append(cmd)
    return cmds

def build_configs(links: List[str]) -> Dict[str, Dict]:
    """回傳 {iface: json_obj} 的 dict。"""
    cfgs = {}
    for l in links:
        iface = LINK_TO_IF[l]
        cfgs[iface] = {
            "Cisco-IOS-XR-ifmgr-cfg:interface": {
                "interface-name": iface,
                "shutdown": [None]
            }
        }
    return cfgs

def write_config_files(configs: Dict[str, Dict], out_dir: Path = Path(".")) -> List[Path]:
    """把 config_<iface>.json 寫檔，回傳檔案路徑清單。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for iface, cfg in configs.items():
        fname = f"config_{iface.replace('/', '_')}.json"
        path = out_dir / fname
        path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
        paths.append(path)
    return paths

def generate(links: List[str], **kwargs) -> Tuple[List[str], Dict[str, Dict]]:
    """
    彙整入口，回傳 (commands, configs)。
      commands : List[str]
      configs  : Dict[iface, cfg_dict]
    """
    cmds = build_commands(links, **kwargs)
    cfgs = build_configs(links)
    return cmds, cfgs
