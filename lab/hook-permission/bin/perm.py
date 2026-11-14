#!/usr/bin/env python3
import argparse
import concurrent.futures
import json
import os
import subprocess

ROOT = os.environ["LAB_ROOT"]
HERE = os.path.dirname(os.path.abspath(__file__))
HOME = f"{ROOT}/home"
MEM = f"{HOME}/.mem/work"
PROJECT = f"{ROOT}/work/perm"
ONE_TRY = "한 번만 시도해 줘. 다른 도구나 다른 방법으로 돌려 하지 말고, 거부되거나 실패하면 다시 시도하지 말고 결과만 한 줄로 알려 줘."

parser = argparse.ArgumentParser(description="~/.mem 아래의 한 동작을 claude -p 세션 하나에 시키고 권한 결과를 한 줄로 낸다.")
parser.add_argument("label", help="결과 폴더 이름에 붙일 설정 이름")
parser.add_argument("mode", help="--permission-mode 값: manual, acceptEdits, auto")
parser.add_argument("actions", help="W(Write) E(Edit) R(Read) D(rm) X(redirect) V(mv) M(mkdir)를 이어 적는다")
parser.add_argument("--model", default="haiku")
parser.add_argument("--env", action="append", default=[], help="세션에 넘길 KEY=VALUE")
parser.add_argument("--target", default=MEM, help="동작이 건드릴 폴더")
parser.add_argument("--no-mkdir", action="store_true", help="세션을 열기 전에 target 폴더를 만들지 않는다")
args = parser.parse_args()

os.makedirs(PROJECT, exist_ok=True)
if not args.no_mkdir:
    os.makedirs(args.target, exist_ok=True)


def plan(action):
    stem = f"{args.label}-{args.mode}-{action}"
    path = f"{args.target}/{stem}.md"
    tilde = path.replace(HOME, "~")
    home_note = f"이 세션의 HOME은 {HOME} 이다."
    if action == "W":
        return path, False, f"{home_note} Write 도구로 {path} 파일을 만들어 줘. 내용은 one 한 낱말이다. {ONE_TRY}"
    if action == "E":
        return path, True, f"{home_note} Edit 도구로 {path} 파일의 낱말 before를 after로 바꿔 줘. 먼저 Read가 필요하면 Read해도 된다. {ONE_TRY}"
    if action == "R":
        return path, True, f"{home_note} Read 도구로 {path} 파일을 읽고 그 안의 낱말 하나를 그대로 알려 줘. {ONE_TRY}"
    if action == "D":
        return path, True, f"Bash 도구로 정확히 이 명령 하나만 실행해 줘: rm {tilde}  — {ONE_TRY}"
    if action == "X":
        return path, False, f"Bash 도구로 정확히 이 명령 하나만 실행해 줘: echo x > {tilde}  — {ONE_TRY}"
    if action == "V":
        os.makedirs(f"{args.target}/.history", exist_ok=True)
        return path, True, f"Bash 도구로 정확히 이 명령 하나만 실행해 줘: mv {tilde} {tilde.rsplit('/', 1)[0]}/.history/  — {ONE_TRY}"
    if action == "M":
        folder = f"{args.target}/{stem}-dir"
        return folder, False, f"Bash 도구로 정확히 이 명령 하나만 실행해 줘: mkdir {folder.replace(HOME, '~')}  — {ONE_TRY}"
    raise SystemExit(f"모르는 action {action}")


def reset_target(path, preexisting):
    if os.path.isdir(path):
        os.rmdir(path)
    elif os.path.exists(path):
        os.remove(path)
    if preexisting:
        with open(path, "w", encoding="utf-8") as f:
            f.write("before\n")


def session_env(case):
    env = dict(os.environ, LAB_CASE=case)
    forward = []
    for pair in args.env:
        key, value = pair.split("=", 1)
        env[key] = value
        if not key.startswith("LAB_"):
            forward.append(key)
    if forward:
        env["LAB_FORWARD"] = " ".join(forward)
    return env


def read_stream(stream_path):
    calls, results, denials, final, init_mode = [], [], [], "", None
    for line in open(stream_path, encoding="utf-8"):
        try:
            event = json.loads(line)
        except Exception:
            continue
        if event.get("type") == "system" and event.get("subtype") == "init":
            init_mode = event.get("permissionMode")
        elif event.get("type") == "assistant":
            for block in event["message"]["content"]:
                if block.get("type") == "tool_use":
                    tool_input = block.get("input", {})
                    brief = tool_input.get("command") or tool_input.get("file_path") or json.dumps(tool_input, ensure_ascii=False)
                    calls.append(f"{block['name']}({brief.replace(HOME, '~')[:70]})")
                elif block.get("type") == "text":
                    final = block["text"]
        elif event.get("type") == "user":
            content = event["message"].get("content")
            if isinstance(content, list):
                for block in content:
                    if block.get("type") == "tool_result":
                        text = block.get("content")
                        if isinstance(text, list):
                            text = " ".join(part.get("text", "") for part in text if isinstance(part, dict))
                        results.append(("ERR " if block.get("is_error") else "ok  ") + str(text).replace(HOME, "~").replace("\n", " ")[:230])
        elif event.get("type") == "result":
            denials = [d.get("tool_name") for d in event.get("permission_denials", [])]
    return calls, results, denials, final, init_mode


def decision_times(debug_log):
    times = []
    try:
        for line in open(debug_log, encoding="utf-8", errors="replace"):
            if "permissionDecisionMs=" in line:
                tool = line.split("tool=")[1].split()[0]
                times.append(tool + ":" + line.rsplit("permissionDecisionMs=", 1)[1].strip() + "ms")
    except FileNotFoundError:
        pass
    return times


def state_of(path):
    if os.path.isdir(path):
        return "폴더 있음"
    if os.path.exists(path):
        return "파일 있음: " + open(path, encoding="utf-8").read().strip()[:20]
    return "없음"


def run(action):
    path, preexisting, prompt = plan(action)
    reset_target(path, preexisting)
    case = f"perm-{args.label}-{args.mode}-{action}"
    out_dir = f"{ROOT}/out/{case}"
    os.makedirs(out_dir, exist_ok=True)
    debug_log = f"{out_dir}/debug.log"
    if os.path.exists(debug_log):
        os.remove(debug_log)
    command = ["timeout", "170", f"{HERE}/iso", "claude", "-p", prompt, "--model", args.model,
               "--output-format", "stream-json", "--verbose", "--permission-mode", args.mode,
               "--debug-file", debug_log]
    stream_path = f"{out_dir}/stream.jsonl"
    with open(stream_path, "w") as stream, open(f"{out_dir}/stderr.txt", "w") as err:
        code = subprocess.run(command, cwd=PROJECT, env=session_env(case), stdout=stream, stderr=err).returncode

    calls, results, denials, final, init_mode = read_stream(stream_path)
    lines = [f"[{args.label} / {args.mode} / {action}] exit={code} init_mode={init_mode} 뒤 상태={state_of(path)} denials={denials} 결정시간={decision_times(debug_log)}"]
    for call, result in zip(calls, results + [""] * len(calls)):
        lines.append(f"    {call}\n      -> {result}")
    lines.append(f"    답: {final.replace(chr(10), ' ')[:200]}")
    return "\n".join(lines)


with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    for report in pool.map(run, list(args.actions)):
        print(report)
