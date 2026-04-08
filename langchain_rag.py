from __future__ import annotations

import argparse
import uuid
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from tinyrag import RagConfig, RagRuntime


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TinyRag: LangChain + FAISS demo")
    parser.add_argument("--question", help="单次提问内容")
    parser.add_argument("--demo", action="store_true", help="运行两个内置演示问题")
    return parser.parse_args()


def run_demo(runtime: RagRuntime) -> None:
    session_id = "demo-session"
    questions = [
        "晚上加班到十点有饭补吗？具体多少？",
        "公司的年假怎么算？",
    ]
    for question in questions:
        result = runtime.invoke(question, session_id=session_id, debug=True)
        print("\n[提问] {0}".format(question))
        print("[回答] {0}".format(result["answer"]))
        if result["rewritten_question"] != question:
            print("[重写] {0}".format(result["rewritten_question"]))
        if result["reloaded"]:
            print("[状态] 检测到知识库变化，已自动重建索引。")
        if result.get("evidence"):
            print("[证据] {0}".format(result["evidence"][0]["source"]))


def interactive_loop(runtime: RagRuntime) -> None:
    session_id = "cli-{0}".format(uuid.uuid4().hex)
    print("进入交互模式，输入 exit 或 quit 退出。")
    while True:
        question = input("\n你: ").strip()
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            break
        result = runtime.invoke(question, session_id=session_id, debug=True)
        print("AI: {0}".format(result["answer"]))
        if result["rewritten_question"] != question:
            print("系统理解: {0}".format(result["rewritten_question"]))
        if result["reloaded"]:
            print("系统: 检测到知识库变化，已自动重建索引。")


def main() -> int:
    load_dotenv()
    args = parse_args()
    config = RagConfig.from_env()
    runtime = RagRuntime(config)
    status = runtime.get_status()

    print("正在准备 RAG 运行时...")
    print("LLM 提供方: {0}".format(config.llm_provider))
    print("知识库路径: {0}".format(config.knowledge_path))
    print("知识库文件数: {0}".format(status["knowledge_file_count"]))

    if args.demo:
        run_demo(runtime)
        return 0

    if args.question:
        result = runtime.invoke(args.question, session_id="single-shot", debug=True)
        print(result["answer"])
        if result["rewritten_question"] != args.question:
            print("系统理解: {0}".format(result["rewritten_question"]))
        if result["reloaded"]:
            print("系统: 检测到知识库变化，已自动重建索引。")
        return 0

    interactive_loop(runtime)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
