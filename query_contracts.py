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
    if len(sys.argv) < 2:
        print("合同查询助手")
        print("用法: python query_contracts.py '您的问题'")
        print("")
        print("示例:")
        print("  python query_contracts.py '申购规则是什么？'")
        print("  python query_contracts.py '投资策略如何？'")
        print("  python query_contracts.py '风险披露在哪里？'")
        print("")
        print("说明: 此脚本专门查询 viking://resources/contract 命名空间下的合同文档")
        return

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

        # Get question from command line
        question = " ".join(sys.argv[1:])
        print(f"合同问题: {question}")
        print("-" * 50)

        ask_contract_question(client, llm, question)

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
