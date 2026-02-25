import logging
import sys
import os
import glob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('add_resources.log')
    ]
)

def add_file_to_openviking(client, file_path, target_uri=None):
    """Add a single file to OpenViking."""
    try:
        logging.info(f"Adding file: {file_path}")
        print(f"正在添加: {os.path.basename(file_path)}")

        # Prepare add_resource parameters
        add_params = {'path': file_path}
        if target_uri:
            add_params['target_uri'] = target_uri
            logging.info(f"Using target_uri: {target_uri}")

        res = client.add_resource(**add_params)
        logging.info(f"add_resource result: {res}")

        if isinstance(res, dict) and 'root_uri' in res:
            print(f"✅ 成功添加: {os.path.basename(file_path)} -> {res['root_uri']}")
            return res['root_uri']
        else:
            print(f"⚠️ 添加完成: {os.path.basename(file_path)} (无root_uri)")
            return None

    except Exception as e:
        logging.error(f"Failed to add {file_path}: {e}")
        print(f"❌ 添加失败: {os.path.basename(file_path)} - {e}")
        return None

def add_directory_to_openviking(client, dir_path, target_uri=None):
    """Add all files in a directory to OpenViking."""
    if not os.path.isdir(dir_path):
        print(f"❌ 目录不存在: {dir_path}")
        return []

    print(f"扫描目录: {dir_path}")
    added_uris = []

    # Find all files (not directories)
    file_pattern = os.path.join(dir_path, "**")
    all_files = glob.glob(file_pattern, recursive=True)
    files_only = [f for f in all_files if os.path.isfile(f)]

    print(f"找到 {len(files_only)} 个文件")

    for file_path in files_only:
        uri = add_file_to_openviking(client, file_path, target_uri)
        if uri:
            added_uris.append(uri)

    return added_uris

def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python add_resources.py <文件路径>")
        print("  python add_resources.py <目录路径>")
        print("  python add_resources.py --target-uri <URI> <文件路径>")
        print("  python add_resources.py --target-uri <URI> <目录路径>")
        print("")
        print("选项:")
        print("  --target-uri <URI>    指定资源添加的目标URI命名空间")
        print("")
        print("示例:")
        print("  python add_resources.py ./docs/contract.pdf")
        print("  python add_resources.py ./docs/")
        print("  python add_resources.py --target-uri viking://my-collection ./docs/")
        print("  python add_resources.py ./docs/file1.pdf ./docs/file2.docx")
        return

    # Parse arguments
    target_uri = None
    paths = []

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--target-uri':
            if i + 1 < len(sys.argv):
                target_uri = sys.argv[i + 1]
                i += 2
            else:
                print("❌ --target-uri 选项需要提供URI值")
                return
        else:
            paths.append(arg)
            i += 1

    if not paths:
        print("❌ 必须指定至少一个文件或目录路径")
        return

    if target_uri:
        print(f"🎯 使用目标URI: {target_uri}")

    try:
        logging.info("Starting resource addition session...")

        # Import modules
        import openviking as ov
        logging.info("OpenViking imported")

        # Initialize OpenViking
        print("初始化 OpenViking...")
        client = ov.OpenViking(path="./data")
        client.initialize()
        logging.info("OpenViking initialized")
        print("✅ OpenViking 初始化完成")

        # Process all arguments
        all_uris = []

        for path in paths:
            if os.path.isdir(path):
                print(f"\n📁 处理目录: {path}")
                uris = add_directory_to_openviking(client, path, target_uri)
                all_uris.extend(uris)
            elif os.path.isfile(path):
                print(f"\n📄 处理文件: {path}")
                uri = add_file_to_openviking(client, path, target_uri)
                if uri:
                    all_uris.append(uri)
            else:
                print(f"❌ 路径不存在: {path}")

        print(f"\n🎉 处理完成!")
        print(f"成功添加了 {len(all_uris)} 个资源")

        if all_uris:
            print("\n添加的资源URI:")
            for uri in all_uris:
                print(f"  - {uri}")

        # Wait for processing
        print("\n⏳ 等待异步处理完成...")
        try:
            client.wait_processed()
            logging.info("Async processing completed")
            print("✅ 异步处理完成")
        except Exception as e:
            logging.warning(f"等待处理时出错: {e}")
            print(f"⚠️ 处理可能仍在后台进行: {e}")

        # Cleanup
        client.close()
        logging.info("Session ended")
        print("✅ 资源添加会话结束")

    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"💥 发生严重错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
