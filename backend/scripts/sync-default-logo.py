import sys
import json
import logging
import argparse
import asyncio
import sqlite3
from pathlib import Path
# python scripts/sync-default-logo.py http://epg.51zmt.top:8000 "table.table" -o output.json
# 添加父目录到系统路径以导入sync模块
sys.path.append(str(Path(__file__).parent.parent))
from sync import extract_table_data
from utils import download_and_save_logo

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('extract_table.log')
    ]
)

def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='从网页中提取表格数据')
    parser.add_argument('url', help='目标网页URL')
    parser.add_argument('selector', help='CSS选择器，用于定位目标表格')
    parser.add_argument('--output', '-o', help='输出文件路径（可选，默认输出到控制台）')
    parser.add_argument('--format', '-f', choices=['json', 'csv'], default='json',
                        help='输出格式（json或csv，默认为json）')

    args = parser.parse_args()

    try:
        # 提取表格数据
        logging.info(f'开始从 {args.url} 提取表格数据')
        data = extract_table_data(args.url, args.selector)
        logging.info(f'成功提取 {len(data)} 行数据')

        # 准备输出
        if args.format == 'json':
            output = json.dumps(data, ensure_ascii=False, indent=2)
        else:  # csv格式
            if not data:
                output = ''
            else:
                headers = list(data[0].keys())
                output = ','.join(headers) + '\n'
                for row in data:
                    output += ','.join(f'"{str(row.get(h, ""))}"' for h in headers) + '\n'

        # 处理图片下载和台标关系
        logo_mapping = {}
        
        # 创建事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 收集所有下载任务
        download_tasks = []
        for item in data:
            if '_href' in item:
                # 将相对URL转换为完整URL
                href = item['_href']
                if href.startswith('./'):
                    href = f'http://epg.51zmt.top:8000{href[1:]}'
                elif not href.startswith('http'):
                    href = f'http://epg.51zmt.top:8000/{href}'
                
                # 创建下载任务
                channel_name = item.get('tvg-name')
                if channel_name:
                    task = download_and_save_logo(href, channel_name)
                    download_tasks.append((channel_name, task))
        
        # 执行所有下载任务
        try:
            # 使用gather执行所有任务
            results = loop.run_until_complete(
                asyncio.gather(
                    *(task for _, task in download_tasks),
                    return_exceptions=True
                )
            )
            
            # 处理下载结果
            for i, result in enumerate(results):
                channel_name = download_tasks[i][0]
                if isinstance(result, Exception):
                    logging.error(f'下载图片失败 {channel_name}: {str(result)}')
                else:
                    logo_mapping[channel_name] = result
                    logging.info(f'已下载图片: {channel_name} -> {result}')
        
        except Exception as e:
            logging.error(f'处理下载任务时出错: {str(e)}')
        finally:
            loop.close()
        
        # 保存台标映射关系到数据库
        conn = None
        cursor = None
        try:
            conn = sqlite3.connect('data/epg.db', check_same_thread=False)
            cursor = conn.cursor()
            
            for channel_name, logo_path in logo_mapping.items():
                # 使用REPLACE INTO确保每个频道只有一条记录
                cursor.execute(
                    "REPLACE INTO default_channel_logos (channel_name, logo_url, priority) VALUES (?, ?, ?)",
                    (channel_name, logo_path, 0)
                )
            
            conn.commit()
            logging.info('已将台标映射关系保存到数据库')
        except Exception as e:
            if conn:
                conn.rollback()
            logging.error(f'保存台标映射关系到数据库时出错: {str(e)}')
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        
        # 输出结果
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            logging.info(f'数据已保存到文件: {args.output}')
        else:
            print(output)

    except Exception as e:
        logging.error(f'处理过程中出现错误: {str(e)}')
        sys.exit(1)

if __name__ == '__main__':
    main()