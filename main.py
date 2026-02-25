import logging
import sys
import os
import faulthandler

# Set environment variable
os.environ['OPENVIKING_CONFIG_FILE'] = './conf/ov.conf'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('main.log')
    ]
)

try:
    logging.info("Script started")
    logging.info(f"OPENVIKING_CONFIG_FILE: {os.environ.get('OPENVIKING_CONFIG_FILE')}")

    logging.info("Importing modules...")
    sys.stdout.flush()

    faulthandler.enable(all_threads=True)
    _import_hang_fp = open("import_hang.log", "a", encoding="utf-8", buffering=1)
    _import_hang_fp.write("\n===== import watchdog armed (15s) =====\n")
    _import_hang_fp.flush()
    faulthandler.dump_traceback_later(15, repeat=True, file=_import_hang_fp)

    try:
        import openviking as ov
        faulthandler.cancel_dump_traceback_later()
        _import_hang_fp.write("===== import openviking finished =====\n")
        _import_hang_fp.flush()
        _import_hang_fp.close()
        logging.info("openviking imported successfully")
    except ImportError as e:
        faulthandler.cancel_dump_traceback_later()
        _import_hang_fp.write("===== import openviking ImportError =====\n")
        _import_hang_fp.flush()
        _import_hang_fp.close()
        logging.error(f"Failed to import openviking: {e}")
        raise
    except Exception as e:
        faulthandler.cancel_dump_traceback_later()
        _import_hang_fp.write("===== import openviking Exception =====\n")
        _import_hang_fp.flush()
        _import_hang_fp.close()
        logging.error(f"Unexpected error importing openviking: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise

    try:
        from openai import OpenAI
        logging.info("openai imported successfully")
    except ImportError as e:
        logging.error(f"Failed to import openai: {e}")
        raise

    logging.info("Initializing OpenViking...")
    # ====== 1️⃣ 初始化 OpenViking ======
    try:
        client = ov.OpenViking(path="./data")
        logging.info("OpenViking client created")
        client.initialize()
        logging.info("OpenViking initialized")
    except Exception as e:
        logging.error(f"Failed to initialize OpenViking: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise

    logging.info("Adding document directory...")
    # ====== 2️⃣ 添加文档目录 ======
    # 可以是目录 / 单文件 / URL
    try:
        res = client.add_resource(path="./docs")
        logging.info(f"add_resource returned: {res}")
        logging.info(f"add_resource type: {type(res)}")
        if hasattr(res, '__dict__'):
            logging.info(f"add_resource attributes: {res.__dict__}")
        if isinstance(res, dict):
            root_uri = res.get("root_uri") or res.get("uri") or res.get("id")
        else:
            root_uri = getattr(res, "root_uri", None) or getattr(res, "uri", None) or getattr(res, "id", None)
        if root_uri is None:
            root_uri = "./docs"  # Fallback to the path itself
        logging.info(f"Document root URI: {root_uri}")
    except Exception as e:
        logging.error(f"Failed to add resource: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise

    print("文档根路径:", root_uri)

    logging.info("Waiting for async processing...")
    # 等待异步处理（生成向量 & L0/L1）
    try:
        client.wait_processed()
        logging.info("Async processing completed")
    except Exception as e:
        logging.error(f"Failed to wait for processing: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise

    logging.info("Setting up user question...")
    # ====== 3️⃣ 用户问题 ======
    question = "申购规则是什么？"
    logging.info(f"Question: {question}")

    logging.info("Performing semantic search...")
    # ====== 4️⃣ 语义检索 ======
    try:
        results = client.find(
            question,
            target_uri=root_uri,
            limit=3
        )
        logging.info(f"Found {len(results.resources)} resources")
    except Exception as e:
        logging.error(f"Failed to search: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise

    print("\n命中资源:")
    for r in results.resources:
        print(f"- {r.uri} (score={r.score:.4f})")

    logging.info("Loading document content...")
    # ====== 5️⃣ 加载原文 L2 内容 ======
    context_blocks = []

    try:
        for r in results.resources:
            logging.info(f"Loading content from: {r.uri}")
            content = client.get(r.uri)  # L2 原文
            context_blocks.append(
                f"\n### 来源: {r.uri}\n{content}"
            )

        context_text = "\n\n".join(context_blocks)
        logging.info(f"Context loaded, total length: {len(context_text)} characters")
    except Exception as e:
        logging.error(f"Failed to load content: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise

    logging.info("Initializing LLM client...")
    # ====== 6️⃣ 调用 LLM ======
    try:
        llm = OpenAI(base_url="https://api.siliconflow.cn/v1",api_key="sk-orwaghbrnozutrubfghzkjfrftautsmizhsasiruceejfstt")
        logging.info("LLM client initialized")
    except Exception as e:
        logging.error(f"Failed to initialize LLM: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise

    logging.info("Creating prompt...")
    prompt = f"""
    你是一个严谨的知识问答助手。

    请基于下面提供的资料回答问题。
    如果资料中没有答案，请明确说"资料中未提及"。

    资料：
    {context_text}

    问题：
    {question}
    """
    logging.info("Prompt created")

    logging.info("Calling LLM...")
    try:
        response = llm.chat.completions.create(
            model="Pro/zai-org/GLM-4.7",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        logging.info("LLM response received")
    except Exception as e:
        logging.error(f"Failed to call LLM: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise

    answer = response.choices[0].message.content
    logging.info("Answer extracted")

    print("\n===== LLM 回答 =====")
    print(answer)

    logging.info("Closing client...")
    try:
        client.close()
        logging.info("Client closed")
    except Exception as e:
        logging.error(f"Failed to close client: {e}")
    
    logging.info("Script completed successfully")

except BaseException as e:
    if isinstance(e, SystemExit):
        logging.error(f"SystemExit occurred: {e}")
    elif isinstance(e, KeyboardInterrupt):
        logging.error(f"KeyboardInterrupt occurred: {e}")
    else:
        logging.error(f"Fatal error occurred: {e}")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    logging.error("Traceback:", exc_info=True)