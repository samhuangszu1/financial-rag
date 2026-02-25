import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def ask_question(client, llm, question):
    """Ask a single question and get answer."""
    logging.info(f"Question: {question}")

    # Perform semantic search
    logging.info("Searching...")
    results = client.find(
        question,
        limit=3
    )
    logging.info(f"Found {len(results.resources)} resources")

    print("\n命中资源:")
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

    # Create prompt
    prompt = f"""
你是一个严谨的知识问答助手。

请基于下面提供的资料回答问题。
如果资料中没有答案，请明确说"资料中未提及"。

资料：
{context_text}

问题：
{question}
"""

    # Call LLM
    logging.info("Calling LLM...")
    response = llm.chat.completions.create(
        model="Pro/zai-org/GLM-4.7",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    answer = response.choices[0].message.content

    print("\n" + "="*50)
    print("回答:")
    print("="*50)
    print(answer)

try:
    logging.info("Starting query session...")
    
    # Import modules
    import openviking as ov
    from openai import OpenAI
    logging.info("Modules imported")

    # Initialize OpenViking with existing data
    logging.info("Loading existing data...")
    client = ov.OpenViking(path="./data")
    client.initialize()
    logging.info("OpenViking initialized")

    # Initialize LLM
    llm = OpenAI(
        base_url="https://api.siliconflow.cn/v1",
        api_key="sk-orwaghbrnozutrubfghzkjfrftautsmizhsasiruceejfstt"
    )

    print("\n" + "="*50)
    print("金融RAG问答系统")
    print("输入问题进行提问，输入 'quit' 或 'exit' 退出")
    print("="*50)

    # Interactive loop
    while True:
        print("\n" + "-"*50)
        try:
            question = input("请输入问题: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n退出程序")
            break
        
        if not question:
            continue
        
        if question.lower() in ('quit', 'exit', 'q', '退出'):
            print("退出程序")
            break
        
        try:
            ask_question(client, llm, question)
        except Exception as e:
            logging.error(f"Error: {e}")
            print(f"处理问题时出错: {e}")

    # Cleanup
    client.close()
    logging.info("Session ended")

except Exception as e:
    logging.error(f"Error: {e}")
    import traceback
    traceback.print_exc()
