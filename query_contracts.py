import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('query_contracts.log')  # Only log to file, not console
    ]
)

def ask_contract_question(client, llm, question):
    """Ask a question about contracts."""
    logging.info(f"Contract question: {question}")
    print("正在搜索合同相关内容...")

    # Perform semantic search within contract namespace
    logging.info("Searching contracts...")
    results = client.find(
        question,
        target_uri="viking://resources/contract",
        limit=5  # Get more results for contracts
    )
    logging.info(f"Found {len(results.resources)} contract resources")
    print(f"找到 {len(results.resources)} 个相关合同文档")

    print("\n命中合同资源:")
    for r in results.resources:
        print(f"- {r.uri} (score={r.score:.4f})")

    # Load content
    context_blocks = []
    for r in results.resources:
        # Skip directory URIs
        if r.uri.startswith("viking://user/memories/"):
            continue

        # Get content from MatchedContext
        content = None
        if hasattr(r, 'overview') and r.overview:
            content = r.overview
        elif hasattr(r, 'abstract') and r.abstract:
            content = r.abstract
        elif hasattr(r, 'content'):
            content = r.content

        if content:
            context_blocks.append(f"\n### 来源: {r.uri}\n{content}")

    context_text = "\n\n".join(context_blocks)
    logging.info(f"Context loaded: {len(context_text)} characters")
    print(f"已加载 {len(context_text)} 字符的合同内容")

    # Create prompt for contract analysis
    prompt = f"""
你是一个专业的合同分析助手，专门处理金融合同相关问题。

请基于下面提供的合同资料回答问题。
如果资料中没有答案，请明确说"资料中未提及"。

合同资料：
{context_text}

问题：
{question}
"""

    # Call LLM
    logging.info("Calling LLM...")
    print("正在分析合同内容并生成回答...")
    try:
        response = llm.chat.completions.create(
            model="Pro/zai-org/GLM-4.7",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            timeout=60
        )
        logging.info("LLM response received")
        print("合同分析完成")
    except Exception as e:
        logging.error(f"LLM call failed: {e}")
        print(f"AI调用失败: {e}")
        return

    answer = response.choices[0].message.content

    print("\n" + "="*50)
    print("合同分析结果:")
    print("="*50)
    print(answer)

def main():
    try:
        logging.info("Starting contract query session...")

        # Import modules
        import openviking as ov
        from openai import OpenAI
        logging.info("Modules imported")

        # Initialize OpenViking with existing data
        logging.info("Loading existing contract data...")
        client = ov.OpenViking(path="./data")
        client.initialize()
        logging.info("OpenViking initialized")

        # Initialize LLM
        llm = OpenAI(
            base_url="https://api.siliconflow.cn/v1",
            api_key="sk-orwaghbrnozutrubfghzkjfrftautsmizhsasiruceejfstt"
        )

        print("\n" + "="*50)
        print("合同智能问答系统")
        print("输入问题进行合同查询，输入 'quit' 或 'exit' 退出")
        print("="*50)

        # Interactive loop for continuous querying
        while True:
            print("\n" + "-"*50)
            try:
                question = input("请输入合同问题: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n退出合同问答系统")
                break
            except UnicodeDecodeError:
                print("检测到编码问题，尝试重新读取...")
                try:
                    import sys
                    if hasattr(sys.stdin, 'buffer'):
                        raw_input = sys.stdin.buffer.readline().decode('utf-8', errors='ignore').strip()
                        question = raw_input
                        print(f"重新读取到输入: {question}")
                    else:
                        print("无法处理编码问题，请使用英文或检查终端设置")
                        continue
                except Exception:
                    print("编码问题无法解决，请使用英文或检查终端设置")
                    continue

            if not question:
                continue

            if question.lower() in ('quit', 'exit', 'q', '退出'):
                print("退出合同问答系统")
                break

            try:
                ask_contract_question(client, llm, question)
            except Exception as e:
                logging.error(f"Error: {e}")
                print(f"处理问题时出错: {e}")

        # Cleanup
        client.close()
        logging.info("Contract query session ended")

    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"发生严重错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
